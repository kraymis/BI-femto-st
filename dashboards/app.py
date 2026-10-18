"""Dashboard Streamlit V2 du pilotage des conventions de stage."""

from pathlib import Path
import re
import sys
from typing import Any
from html import escape

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bi.analytics import (  # noqa: E402
    convention_crosstab,
    count_conventions,
    count_conventions_by_category,
    count_students,
    crosstab_row_percentages,
    crosstab_with_totals,
    field_coverage,
    filter_aggregated_categories,
    filter_stages,
    aggregate_geography,
    GeographicReferenceError,
    load_geographic_reference,
    quality_summary,
    yearly_field_coverage,
)
from bi.config import (  # noqa: E402
    GEOGRAPHIC_MIN_CONVENTIONS_PER_DESTINATION,
    GEOGRAPHIC_REFERENCE_FILE,
    SCHOOL_ADDRESS,
    SCHOOL_COORDINATES_SOURCE,
    SCHOOL_COORDINATES_VERIFIED_ON,
    SCHOOL_LATITUDE,
    SCHOOL_LONGITUDE,
    SCHOOL_NAME,
    STAGES_SOURCE_FILE,
)
from bi.ingestion import DataFileError, MissingColumnsError, load_stages  # noqa: E402


REQUIRED_APP_COLUMNS = (
    "n_convention_de_stage",
    "n_etudiant",
    "annee_academique",
    "type_de_stage",
    "nature_du_stage",
)
OPTIONAL_QUALITY_FIELDS = (
    "entreprise",
    "entreprise_lieu_stage",
    "date_debut",
    "date_fin",
    "pays_lieu_stage",
    "ville_lieu_stage",
    "cp_lieu_stage",
    "ville",
    "code_postal",
    "date_soutenance",
)
OPTIONAL_SOURCE_COLUMNS = tuple(
    field
    for field in OPTIONAL_QUALITY_FIELDS
    if field not in REQUIRED_APP_COLUMNS
)
QUALITY_FIELDS = (
    "annee_academique",
    "type_de_stage",
    "nature_du_stage",
    "entreprise",
    "entreprise_lieu_stage",
    "date_debut",
    "date_fin",
    "pays_lieu_stage",
    "ville_lieu_stage",
    "cp_lieu_stage",
    "ville",
    "code_postal",
    "date_soutenance",
)
MISSING_LABEL = "Non renseigné"
FILTERS = (
    ("academic_years", "Année académique", "annee_academique"),
    ("stage_types", "Type de stage", "type_de_stage"),
    ("stage_natures", "Nature du stage", "nature_du_stage"),
)
FIELD_LABELS = {
    "annee_academique": "Année académique",
    "type_de_stage": "Type de stage",
    "nature_du_stage": "Nature du stage",
    "entreprise": "Organisme — entreprise",
    "entreprise_lieu_stage": "Entreprise du lieu de stage",
    "date_debut": "Date de début",
    "date_fin": "Date de fin",
    "pays_lieu_stage": "Pays du lieu de stage",
    "ville_lieu_stage": "Ville du lieu de stage",
    "cp_lieu_stage": "Code postal du lieu de stage",
    "ville": "Ville — champ général",
    "code_postal": "Code postal — champ général",
    "date_soutenance": "Date de soutenance",
}
PAGE_NAMES = (
    "Vue d’ensemble",
    "Analyse temporelle",
    "Analyse des stages",
    "Entreprises et géographie",
    "Qualité des données",
)
DESTINATION_MARKER_HTML = (
    '<div style="width:16px;height:16px;background:#246B9E;'
    "border:2px solid #FFFFFF;border-radius:50% 50% 50% 0;"
    "transform:rotate(-45deg);box-shadow:0 1px 4px #333;"
    '"><div style="width:4px;height:4px;margin:4px;background:#FFFFFF;'
    'border-radius:50%;"></div></div>'
)
PLOTLY_ERROR = (
    "Les graphiques interactifs nécessitent Plotly. "
    "Installez les dépendances avec `python -m pip install -r requirements.txt`."
)


def _plotly_express() -> Any | None:
    try:
        import plotly.express as px
    except ImportError:
        return None
    return px


def _missing_label_for(values: list[object]) -> str:
    label = MISSING_LABEL
    while label in values:
        label = f"{label} (valeur absente)"
    return label


def _filter_options(data: pd.DataFrame, column: str) -> tuple[list[object], str]:
    values = list(data[column].dropna().drop_duplicates())
    missing_label = _missing_label_for(values)
    options = values.copy()
    if data[column].isna().any():
        options.append(missing_label)
    return options, missing_label


def _reset_global_filters(options_by_key: dict[str, list[object]]) -> None:
    for key, options in options_by_key.items():
        st.session_state[key] = options.copy()


def _prepare_filter_state(key: str, options: list[object]) -> None:
    if key not in st.session_state:
        st.session_state[key] = options.copy()
        return
    allowed = set(options)
    st.session_state[key] = [
        value for value in st.session_state[key] if value in allowed
    ]


def _render_global_filters(data: pd.DataFrame) -> pd.DataFrame:
    options_by_key: dict[str, list[object]] = {}
    selected_by_key: dict[str, list[object]] = {}
    missing_labels: dict[str, str] = {}
    filter_columns = st.columns(3)

    for container, (key, label, column) in zip(filter_columns, FILTERS):
        options, missing_label = _filter_options(data, column)
        options_by_key[key] = options
        missing_labels[key] = missing_label
        _prepare_filter_state(key, options)
        selected_by_key[key] = container.multiselect(
            label,
            options=options,
            key=key,
            help="Les valeurs absentes sont proposées séparément.",
        )

    st.button(
        "Réinitialiser les filtres",
        on_click=_reset_global_filters,
        kwargs={"options_by_key": options_by_key},
        help="Rétablit toutes les modalités, y compris les valeurs non renseignées.",
    )

    filter_args: dict[str, Any] = {}
    argument_names = {
        "academic_years": ("academic_years", "include_missing_year"),
        "stage_types": ("stage_types", "include_missing_type"),
        "stage_natures": ("stage_natures", "include_missing_nature"),
    }
    for key, selected in selected_by_key.items():
        missing_label = missing_labels[key]
        selected_values = [
            value for value in selected if value != missing_label
        ]
        if missing_label in selected:
            selected_values.append(None)
        values_argument, missing_argument = argument_names[key]
        filter_args[values_argument] = selected_values
        filter_args[missing_argument] = False

    return filter_stages(data, **filter_args)


def _format_count(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _format_percentage(value: object, decimals: int = 1) -> str:
    if pd.isna(value):
        return "Non calculable"
    return f"{float(value):.{decimals}f} %".replace(".", ",")


def _category_counts(data: pd.DataFrame, column: str) -> pd.DataFrame:
    result = count_conventions_by_category(data, column).copy()
    values = list(data[column].dropna().drop_duplicates())
    missing_label = _missing_label_for(values)
    result["label"] = result.apply(
        lambda row: missing_label
        if row["category_is_missing"]
        else str(row["category"]),
        axis=1,
    )
    return result


def _academic_sort_key(label: object) -> tuple[int, int, str]:
    match = re.fullmatch(r"(\d{4})/(\d{4})", str(label))
    if match:
        return int(match.group(1)), int(match.group(2)), str(label)
    return (10**9, 10**9, str(label))


def _sort_year_categories(data: pd.DataFrame, column: str) -> pd.DataFrame:
    if data.empty or column not in data.columns:
        return data
    return data.sort_values(
        by=column,
        key=lambda values: values.map(_academic_sort_key),
        kind="stable",
    )


def _localized_coverage(
    data: pd.DataFrame, available_fields: list[str]
) -> pd.DataFrame:
    coverage = field_coverage(data, available_fields).copy()
    coverage["Champ"] = coverage["field"].map(FIELD_LABELS).fillna(
        coverage["field"]
    )
    coverage["Valeurs renseignées"] = coverage.apply(
        lambda row: (
            f"{_format_count(int(row['present_count']))} / "
            f"{_format_count(int(row['denominator']))}"
        ),
        axis=1,
    )
    coverage["Valeurs manquantes"] = coverage["missing_count"].map(
        lambda value: _format_count(int(value))
    )
    coverage["Couverture"] = coverage["completion_percentage"].map(
        _format_percentage
    )
    return coverage[
        ["Champ", "Valeurs renseignées", "Valeurs manquantes", "Couverture"]
    ]


def _active_filter_summary() -> str:
    selections = []
    for key, label, _ in FILTERS:
        selected = st.session_state.get(key, [])
        if selected:
            selections.append(f"{label} : {len(selected)} modalité(s)")
    if not selections:
        return "Filtres actifs : aucun — toutes les modalités sont incluses."
    return "Filtres actifs : " + " · ".join(selections)


def _render_plot(figure: Any, **kwargs: Any) -> None:
    if figure is None:
        return
    if _plotly_express() is None:
        st.warning(PLOTLY_ERROR)
        return
    st.plotly_chart(
        figure,
        width="stretch",
        theme=None,
        config={"displaylogo": False, "responsive": True},
        **kwargs,
    )


def _bar_figure(
    data: pd.DataFrame,
    category_column: str,
    value_column: str,
    title: str,
    value_label: str,
    horizontal: bool = False,
    color: str = "#245A81",
) -> Any | None:
    if data.empty or _plotly_express() is None:
        if not data.empty:
            st.warning(PLOTLY_ERROR)
        return None
    px = _plotly_express()
    if horizontal:
        figure = px.bar(
            data,
            x=value_column,
            y=category_column,
            orientation="h",
            title=title,
            labels={value_column: value_label, category_column: ""},
            text=value_column,
            color_discrete_sequence=[color],
        )
        figure.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        figure = px.bar(
            data,
            x=category_column,
            y=value_column,
            title=title,
            labels={value_column: value_label, category_column: ""},
            text=value_column,
            color_discrete_sequence=[color],
        )
    figure.update_traces(
        hovertemplate="%{x}<br>%{y}<extra></extra>",
        textposition="outside",
    )
    figure.update_layout(
        template="plotly_white",
        margin={"l": 20, "r": 20, "t": 55, "b": 30},
        font={"family": "Arial, sans-serif", "color": "#18324B"},
        title={"x": 0.02, "xanchor": "left"},
        showlegend=False,
    )
    return figure


def _crosstab_for_display(
    data: pd.DataFrame,
    row_column: str,
    column_column: str,
    measure: str,
) -> pd.DataFrame:
    counts = convention_crosstab(data, row_column, column_column)
    if measure == "Pourcentages par ligne":
        displayed = crosstab_row_percentages(counts)
        displayed = displayed.apply(
            lambda column: column.map(
                lambda value: "Non calculable"
                if pd.isna(value)
                else _format_percentage(value)
            )
        )
        displayed["Total de ligne"] = displayed.apply(
            lambda row: "100,0 %" if row.notna().any() else "Non calculable",
            axis=1,
        )
        return displayed

    displayed = crosstab_with_totals(counts)
    return displayed.apply(
        lambda column: column.map(lambda value: _format_count(int(value)))
    )


def _render_empty_state() -> None:
    st.info(
        "Aucune convention ne correspond aux filtres sélectionnés. "
        "Modifiez la sélection ou réinitialisez les filtres."
    )


def _render_overview(data: pd.DataFrame) -> None:
    st.title("Vue d’ensemble")
    st.caption(
        "Repères de pilotage calculés sur les conventions du périmètre sélectionné."
    )
    if data.empty:
        _render_empty_state()
        return

    academic_year_count = int(data["annee_academique"].nunique(dropna=True))
    type_count = int(data["type_de_stage"].nunique(dropna=True))
    metrics = st.columns(4)
    metrics[0].metric(
        "Conventions distinctes",
        _format_count(count_conventions(data)),
        help="Décompte distinct des numéros de convention. Ce n’est pas un nombre de stages validé.",
    )
    metrics[1].metric(
        "Étudiants distincts",
        _format_count(count_students(data)),
        help="Décompte distinct des identifiants, sans affichage de ceux-ci.",
    )
    metrics[2].metric(
        "Années académiques renseignées",
        _format_count(academic_year_count),
    )
    metrics[3].metric(
        "Types de stage renseignés",
        _format_count(type_count),
        help="Les catégories non renseignées ne sont pas comptées comme un type.",
    )

    st.caption(
        f"Périmètre : {_format_count(len(data))} lignes · "
        f"{_format_count(count_conventions(data))} conventions distinctes."
    )
    st.caption(_active_filter_summary())
    st.warning(
        "La dernière année académique observée peut être incomplète. "
        "Aucune comparaison de périodes ni mesure de durée n’est publiée."
    )

    year_counts = _category_counts(data, "annee_academique")
    year_counts = _sort_year_categories(year_counts, "category")
    type_counts = _category_counts(data, "type_de_stage")
    nature_counts = _category_counts(data, "nature_du_stage")
    type_counts = type_counts.sort_values(
        "convention_count", ascending=False, kind="stable"
    )
    nature_counts = nature_counts.sort_values(
        "convention_count", ascending=False, kind="stable"
    )

    st.subheader("Évolution des conventions")
    _render_plot(
        _bar_figure(
            year_counts,
            "label",
            "convention_count",
            "Conventions distinctes par année académique",
            "Conventions distinctes",
            color="#245A81",
        )
    )
    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.subheader("Répartition par type")
        _render_plot(
            _bar_figure(
                type_counts,
                "label",
                "convention_count",
                "Conventions par type de stage",
                "Conventions distinctes",
                horizontal=True,
                color="#3B78A1",
            )
        )
    with chart_columns[1]:
        st.subheader("Répartition par nature")
        _render_plot(
            _bar_figure(
                nature_counts,
                "label",
                "convention_count",
                "Conventions par nature de stage",
                "Conventions distinctes",
                horizontal=True,
                color="#50886C",
            )
        )
    st.caption(
        "Les valeurs manquantes apparaissent comme « Non renseigné ». "
        "Les catégories ne sont pas fusionnées."
    )


def _render_temporal_analysis(data: pd.DataFrame) -> None:
    st.title("Analyse temporelle")
    st.caption(
        "Répartition descriptive des conventions au fil des années académiques."
    )
    if data.empty:
        _render_empty_state()
        return

    measure = st.radio(
        "Mesure des tableaux croisés",
        options=("Effectifs", "Pourcentages par ligne"),
        horizontal=True,
        key="temporal_measure",
        help=(
            "Les pourcentages sont calculés au sein de chaque année, "
            "sur les cellules du tableau croisé."
        ),
    )
    counts = _category_counts(data, "annee_academique")
    counts = _sort_year_categories(counts, "category")
    st.subheader("Conventions par année")
    _render_plot(
        _bar_figure(
            counts,
            "label",
            "convention_count",
            "Conventions distinctes par année académique",
            "Conventions distinctes",
            color="#245A81",
        )
    )

    crosstab = convention_crosstab(
        data, "annee_academique", "type_de_stage"
    )
    crosstab = crosstab.reindex(
        sorted(crosstab.index, key=_academic_sort_key)
    )
    if measure == "Pourcentages par ligne":
        row_values = crosstab_row_percentages(crosstab)
        stacked_data = (
            row_values.rename_axis("Année académique")
            .reset_index()
            .melt(
                id_vars="Année académique",
                var_name="Type de stage",
                value_name="Pourcentage",
            )
        )
        stacked_value_column = "Pourcentage"
        stacked_label = "Pourcentage par année"
    else:
        stacked_data = (
            crosstab.rename_axis("Année académique")
            .reset_index()
            .melt(
                id_vars="Année académique",
                var_name="Type de stage",
                value_name="Conventions distinctes",
            )
        )
        stacked_value_column = "Conventions distinctes"
        stacked_label = "Conventions distinctes"

    st.subheader("Composition annuelle par type")
    px = _plotly_express()
    if px is None:
        st.warning(PLOTLY_ERROR)
    elif not stacked_data.empty:
        figure = px.bar(
            stacked_data,
            x="Année académique",
            y=stacked_value_column,
            color="Type de stage",
            barmode="stack",
            title="Types de stage au sein de chaque année",
            labels={stacked_value_column: stacked_label},
            color_discrete_sequence=(
                px.colors.qualitative.Safe
            ),
        )
        figure.update_layout(template="plotly_white")
        _render_plot(figure)

    st.subheader("Tableau croisé — année × type")
    if measure == "Pourcentages par ligne":
        st.caption(
            "Chaque ligne totalise 100 % de son dénominateur, à l’arrondi près. "
            "Le dénominateur est la somme des cellules par type pour cette année."
        )
    try:
        st.dataframe(
            _crosstab_for_display(
                data, "annee_academique", "type_de_stage", measure
            ),
            width="stretch",
        )
    except ValueError as exc:
        st.warning(f"Tableau croisé indisponible : {exc}")

    st.subheader("Composition relative au sein de chaque année")
    composition = crosstab_row_percentages(crosstab).reset_index()
    st.dataframe(
        composition,
        hide_index=True,
        width="stretch",
    )
    st.warning(
        "L’année académique la plus récente est susceptible d’être incomplète. "
        "Les volumes ne constituent pas une comparaison de périodes complètes."
    )


def _render_stage_analysis(data: pd.DataFrame) -> None:
    st.title("Analyse des stages")
    st.caption(
        "Composition par type et nature ; les effectifs comptent des conventions distinctes."
    )
    if data.empty:
        _render_empty_state()
        return

    measure = st.radio(
        "Mesure des classements et tableaux",
        options=("Effectifs", "Pourcentages par ligne"),
        horizontal=True,
        key="stage_measure",
    )
    top_n = st.selectbox(
        "Nombre maximal de catégories affichées par classement",
        options=(5, 10, 20, 50),
        index=1,
    )
    category_search = st.text_input(
        "Rechercher une catégorie",
        help="Recherche dans les catégories agrégées, sans accès aux lignes individuelles.",
    )

    type_counts = _category_counts(data, "type_de_stage").sort_values(
        "convention_count", ascending=False, kind="stable"
    )
    nature_counts = _category_counts(data, "nature_du_stage").sort_values(
        "convention_count", ascending=False, kind="stable"
    )
    type_counts = filter_aggregated_categories(
        type_counts, ["label"], category_search
    )
    nature_counts = filter_aggregated_categories(
        nature_counts, ["label"], category_search
    )

    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.subheader("Types de stage")
        shown_types = type_counts.head(top_n)
        _render_plot(
            _bar_figure(
                shown_types,
                "label",
                "convention_count",
                "Conventions par type",
                "Conventions distinctes",
                horizontal=True,
                color="#3B78A1",
            )
        )
        st.caption(
            f"{len(shown_types)} catégorie(s) affichée(s) sur "
            f"{len(type_counts)} après recherche ; les autres ne sont pas regroupées."
        )
    with chart_columns[1]:
        st.subheader("Natures de stage")
        shown_natures = nature_counts.head(top_n)
        _render_plot(
            _bar_figure(
                shown_natures,
                "label",
                "convention_count",
                "Conventions par nature",
                "Conventions distinctes",
                horizontal=True,
                color="#50886C",
            )
        )
        st.caption(
            f"{len(shown_natures)} catégorie(s) affichée(s) sur "
            f"{len(nature_counts)} après recherche ; les autres ne sont pas regroupées."
        )

    st.subheader("Tableau croisé — type × nature")
    cross_tab = convention_crosstab(data, "type_de_stage", "nature_du_stage")
    if measure == "Pourcentages par ligne":
        st.caption(
            "Chaque ligne totalise 100 % de son dénominateur, à l’arrondi près. "
            "Le dénominateur est la somme des cellules par nature pour ce type."
        )
    try:
        st.dataframe(
            _crosstab_for_display(
                data, "type_de_stage", "nature_du_stage", measure
            ),
            width="stretch",
        )
    except ValueError as exc:
        st.warning(f"Tableau croisé indisponible : {exc}")
    st.caption(
        f"Tableau croisé calculé sur {cross_tab.shape[0]} type(s) et "
        f"{cross_tab.shape[1]} nature(s), valeurs inconnues incluses."
    )

    st.subheader("Récapitulatif des catégories")
    category_table = pd.concat(
        [
            type_counts.assign(categorie="Type"),
            nature_counts.assign(categorie="Nature"),
        ],
        ignore_index=True,
    )
    category_table["Part du total"] = category_table["percentage"].map(
        _format_percentage
    )
    st.dataframe(
        category_table[
            ["categorie", "label", "convention_count", "denominator", "Part du total"]
        ].rename(
            columns={
                "categorie": "Famille",
                "label": "Catégorie",
                "convention_count": "Conventions distinctes",
                "denominator": "Dénominateur",
            }
        ),
        hide_index=True,
        width="stretch",
    )
    if not category_search:
        st.caption(
            "Le sélecteur Top N limite uniquement les graphiques ; "
            "le tableau récapitulatif conserve toutes les catégories."
        )


def _render_exploration_page(data: pd.DataFrame) -> None:
    st.title("Entreprises et géographie")
    st.caption(
        "Exploration descriptive des libellés d’entreprise et des lieux renseignés."
    )
    if data.empty:
        _render_empty_state()
        return

    st.warning(
        "Ces résultats sont exploratoires : la définition de l’entreprise d’accueil "
        "reste à valider. Le seuil d’affichage géographique est configuré à "
        f"{GEOGRAPHIC_MIN_CONVENTIONS_PER_DESTINATION} conventions par destination ; "
        "sa validation institutionnelle reste nécessaire avant diffusion. "
        "Aucun export n’est disponible."
    )
    available_fields = [
        field
        for field in (
            "entreprise",
            "entreprise_lieu_stage",
            "pays_lieu_stage",
            "ville_lieu_stage",
            "cp_lieu_stage",
            "ville",
            "code_postal",
        )
        if field in data.columns
    ]
    st.subheader("Couverture des champs d’entreprise et de localisation")
    st.dataframe(
        _localized_coverage(data, available_fields),
        hide_index=True,
        width="stretch",
    )

    company_column = "entreprise"
    if company_column not in data.columns:
        st.info(
            "Le champ `entreprise` n’est pas disponible ; "
            "aucune analyse d’entreprise n’est produite."
        )
    else:
        st.subheader("Libellés d’entreprise — exploration")
        st.caption(
            "Source utilisée : `entreprise`. Les libellés distincts ne sont pas "
            "des entités juridiques validées et ne sont pas fusionnés."
        )
        company_counts = _category_counts(data, company_column)
        company_counts = company_counts.loc[
            ~company_counts["category_is_missing"]
        ].sort_values(
            "convention_count", ascending=False, kind="stable"
        )
        company_query = st.text_input(
            "Rechercher un libellé d’entreprise",
            key="company_search",
        )
        company_counts = filter_aggregated_categories(
            company_counts, ["label"], company_query
        )
        company_top_n = st.selectbox(
            "Libellés d’entreprise à afficher",
            options=(5, 10, 20),
            index=1,
            key="company_top_n",
        )
        company_counts = company_counts.head(company_top_n)
        _render_plot(
            _bar_figure(
                company_counts,
                "label",
                "convention_count",
                "Conventions par libellé d’entreprise",
                "Conventions distinctes",
                horizontal=True,
                color="#557C9E",
            )
        )
        st.caption(
            "Les conventions sans libellé d’entreprise restent dans le périmètre "
            "global, mais ne figurent pas dans ce classement."
        )

    country_column = "pays_lieu_stage"
    st.subheader("Destinations par pays")
    if country_column not in data.columns:
        st.info(
            "Le champ `pays_lieu_stage` est absent ; "
            "la répartition géographique n’est pas calculable."
        )
    else:
        country_coverage = field_coverage(data, [country_column]).iloc[0]
        st.metric(
            "Pays du lieu renseigné",
            (
                f"{_format_count(int(country_coverage['present_count']))} / "
                f"{_format_count(int(country_coverage['denominator']))} lignes"
            ),
            help=(
                "Indicateur de couverture au niveau ligne ; il ne représente "
                "pas un nombre de conventions."
            ),
        )
        if GEOGRAPHIC_MIN_CONVENTIONS_PER_DESTINATION is None:
            st.info(
                "La répartition détaillée par pays est désactivée tant qu’un "
                "seuil de confidentialité n’a pas été approuvé."
            )

    _render_geographic_analysis(data)


def _render_geographic_analysis(data: pd.DataFrame) -> None:
    st.subheader("Couverture géographique et distances")
    st.caption(
        "Destination calculée uniquement avec `ville_lieu_stage` et "
        "`pays_lieu_stage`. Les champs `ville` et `code_postal` ne sont pas "
        "utilisés pour localiser les stages."
    )
    st.warning(
        "Le choix des colonnes suffixées `_lieu_stage` est provisoire : "
        "l’audit demande encore de confirmer leur sémantique avec le métier "
        "avant toute interprétation publiée."
    )
    if not GEOGRAPHIC_REFERENCE_FILE.is_file():
        st.info(
            "Le référentiel local de coordonnées n’existe pas encore. "
            "La carte et les distances sont indisponibles jusqu’à sa préparation."
        )
        st.code(
            "$env:PYTHONPATH = (Join-Path (Get-Location).Path 'src')\n"
            ".venv\\Scripts\\python.exe -m bi.preprocessing.geographic_reference",
            language="powershell",
        )
        st.caption(
            f"Référence de l’école : {SCHOOL_NAME} — {SCHOOL_ADDRESS}. "
            f"Coordonnées fixes vérifiées le {SCHOOL_COORDINATES_VERIFIED_ON} "
            f"sur le site officiel : {SCHOOL_COORDINATES_SOURCE}."
        )
        return

    required_location_columns = ("ville_lieu_stage", "pays_lieu_stage")
    missing_columns = [
        field for field in required_location_columns if field not in data.columns
    ]
    if missing_columns:
        st.warning(
            "L’analyse géographique ne peut pas être calculée : "
            f"colonnes de destination absentes ({', '.join(missing_columns)})."
        )
        return

    try:
        reference = load_geographic_reference(GEOGRAPHIC_REFERENCE_FILE)
        result = aggregate_geography(data, reference)
    except GeographicReferenceError as exc:
        st.warning(f"Référentiel géographique indisponible : {exc}")
        return
    except ValueError as exc:
        st.warning(f"Analyse géographique indisponible : {exc}")
        return

    summary = result.summary
    metric_columns = st.columns(3)
    metric_columns[0].metric(
        "Conventions distinctes du périmètre",
        _format_count(int(summary["total_conventions"])),
    )
    metric_columns[1].metric(
        "Conventions associées à des coordonnées valides",
        (
            f"{_format_count(int(summary['located_conventions']))} / "
            f"{_format_count(int(summary['total_conventions']))}"
        ),
        help="Dénominateur : conventions distinctes du périmètre filtré.",
    )
    metric_columns[2].metric(
        "Couverture géographique",
        _format_percentage(summary["coverage_percentage"]),
        help="Conventions aux coordonnées validées / conventions distinctes.",
    )
    additional_metrics = st.columns(4)
    additional_metrics[0].metric(
        "Conventions avec destination source exploitable",
        _format_count(int(summary["destination_available_conventions"])),
        help=(
            "Une seule ville+pays distincte est présente pour la convention ; "
            "cela ne garantit pas que les coordonnées soient connues."
        ),
    )
    additional_metrics[1].metric(
        "Conventions non localisées",
        _format_count(int(summary["not_located_conventions"])),
    )
    additional_metrics[2].metric(
        "Destinations distinctes localisées",
        _format_count(int(summary["localized_destinations"])),
    )
    additional_metrics[3].metric(
        "Conventions sans pays renseigné",
        _format_count(int(summary["missing_country_conventions"])),
    )
    if (
        summary["total_conventions"]
        and int(summary["located_conventions"])
        <= int(summary["total_conventions"]) / 2
    ):
        st.warning(
            "La majorité des conventions ne peut pas être localisée. "
            "Les résultats géographiques ne sont pas représentatifs de "
            "l’ensemble du périmètre."
        )
    if int(summary["ambiguous_conventions"]):
        st.warning(
            f"{_format_count(int(summary['ambiguous_conventions']))} convention(s) "
            "associée(s) à plusieurs destinations sont exclues des distances."
        )
    if int(summary["ambiguous_country_conventions"]):
        st.warning(
            f"{_format_count(int(summary['ambiguous_country_conventions']))} "
            "convention(s) associée(s) à plusieurs pays sont exclues de la "
            "répartition par pays."
        )

    st.caption(
        "La distance estimée à vol d’oiseau depuis SUPMICROTECH-ENSMM "
        "n’est ni une distance routière ni une mesure exacte jusqu’à l’entreprise."
    )
    statuses = result.status_counts.copy()
    statuses["Conventions"] = statuses["convention_count"].map(
        lambda value: _format_count(int(value))
    )
    statuses["Dénominateur"] = statuses["denominator"].map(
        lambda value: _format_count(int(value))
    )
    statuses["Part"] = statuses["percentage"].map(_format_percentage)
    st.dataframe(
        statuses[["label", "Conventions", "Dénominateur", "Part"]].rename(
            columns={"label": "État géographique"}
        ),
        hide_index=True,
        width="stretch",
    )

    threshold = GEOGRAPHIC_MIN_CONVENTIONS_PER_DESTINATION
    if threshold is None:
        st.warning(
            "La carte, le classement des destinations, la répartition par pays "
            "et les classes de distance sont masqués : aucun seuil de confidentialité "
            "n’a été approuvé. La couverture agrégée ci-dessus reste disponible."
        )
        return
    if threshold < 1:
        st.error(
            "Le seuil de confidentialité doit être un entier supérieur ou égal à 1."
        )
        return

    destinations = result.destinations.loc[
        result.destinations["convention_count"] >= threshold
    ].copy()
    if destinations.empty:
        st.info(
            "Aucune destination ne satisfait le seuil de confidentialité configuré."
        )
        return

    st.subheader("Destinations localisées")
    try:
        import folium
        from folium.plugins import MarkerCluster
        from streamlit_folium import st_folium
    except ImportError:
        st.warning(
            "La carte nécessite Folium et streamlit-folium. "
            "Installez les dépendances déclarées dans requirements.txt."
        )
    else:
        map_view = folium.Map(
            location=[SCHOOL_LATITUDE, SCHOOL_LONGITUDE],
            zoom_start=5,
            control_scale=True,
            tiles="OpenStreetMap",
        )
        cluster = MarkerCluster(
            name="Destinations de stage (agrégées)"
        ).add_to(map_view)
        map_bounds = [[SCHOOL_LATITUDE, SCHOOL_LONGITUDE]]
        for destination in destinations.itertuples(index=False):
            city = escape(str(destination.city))
            country = escape(str(destination.country or "Non renseigné"))
            companies = getattr(destination, "companies", [])
            company_list = (
                "<br>".join(escape(str(company)) for company in companies)
                if companies
                else "Non renseigné"
            )
            stage_ids = getattr(destination, "stage_ids", [])
            stage_id_list = (
                "<br>".join(escape(str(stage_id)) for stage_id in stage_ids)
                if stage_ids
                else "Non renseigné"
            )
            popup = (
                f"<b>Ville :</b> {city}<br>"
                f"<b>Pays :</b> {country}<br>"
                f"<b>Conventions distinctes :</b> "
                f"{_format_count(int(destination.convention_count))}<br>"
                f"<b>Entreprises renseignées :</b><br>{company_list}<br>"
                f"<b>Numéros de convention associés :</b><br>"
                f"{stage_id_list}<br>"
                f"<b>Distance estimée à vol d’oiseau depuis "
                f"SUPMICROTECH-ENSMM :</b> {destination.distance_km:.1f} km"
            )
            folium.Marker(
                location=[destination.latitude, destination.longitude],
                icon=folium.DivIcon(
                    html=DESTINATION_MARKER_HTML,
                    icon_size=(20, 20),
                    icon_anchor=(10, 18),
                    class_name="destination-marker",
                ),
                tooltip=f"{city}, {country}",
                popup=folium.Popup(popup, max_width=360),
            ).add_to(cluster)
            map_bounds.append([destination.latitude, destination.longitude])

        folium.CircleMarker(
            location=[SCHOOL_LATITUDE, SCHOOL_LONGITUDE],
            radius=9,
            color="#B22222",
            fill=True,
            fill_color="#B22222",
            fill_opacity=1,
            tooltip=f"{SCHOOL_NAME} — établissement de référence",
            popup=folium.Popup(
                f"<b>{escape(SCHOOL_NAME)}</b><br>"
                f"{escape(SCHOOL_ADDRESS)}",
                max_width=360,
            ),
        ).add_to(map_view)
        map_view.fit_bounds(map_bounds, padding=(20, 20))
        folium.LayerControl().add_to(map_view)
        st_folium(
            map_view,
            height=560,
            width=1200,
            returned_objects=[],
            key="geographic_destination_map",
        )
        st.caption(
            "Les marqueurs représentent des destinations, pas des étudiants ni "
            "des conventions individuelles. Le fond OpenStreetMap nécessite un "
            "accès réseau ; coordonnées et distances proviennent du référentiel local."
        )

    st.subheader("Distances par classe")
    st.caption(
        "Classes descriptives ; pourcentages parmi les conventions localisées "
        "et dénominateur indiqué. Les catégories sous le seuil ne sont pas affichées."
    )
    visible_bands = result.distance_bands.loc[
        result.distance_bands["convention_count"] >= threshold
    ].copy()
    if visible_bands.empty:
        st.info("Aucune classe de distance ne satisfait le seuil configuré.")
    else:
        st.dataframe(
            visible_bands.rename(
                columns={
                    "distance_band": "Classe de distance",
                    "convention_count": "Conventions distinctes",
                    "denominator": "Dénominateur — conventions localisées",
                    "percentage": "Part parmi les conventions localisées (%)",
                }
            ),
            hide_index=True,
            width="stretch",
        )

    st.subheader("Destinations les plus fréquentes")
    top_n = st.selectbox(
        "Nombre de destinations à afficher",
        options=(5, 10, 20),
        index=1,
        key="geographic_destination_top_n",
    )
    ranked = destinations.sort_values(
        "convention_count", ascending=False, kind="stable"
    ).head(top_n)
    ranked["distance_km"] = ranked["distance_km"].map(
        lambda value: f"{float(value):.1f} km".replace(".", ",")
    )
    st.dataframe(
        ranked[
            ["city", "country", "convention_count", "distance_km"]
        ].rename(
            columns={
                "city": "Ville",
                "country": "Pays",
                "convention_count": "Conventions distinctes",
                "distance_km": "Distance estimée à vol d’oiseau",
            }
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        f"Le tableau affiche les {len(ranked)} première(s) destination(s) "
        f"parmi {len(destinations)} satisfaisant le seuil ; les autres destinations "
        "au-dessus du seuil ne sont pas dans le Top N. Les destinations sous le "
        "seuil sont entièrement masquées. Ce n’est pas un classement d’entreprises."
    )

    st.subheader("Conventions par pays du lieu")
    country_rows = result.countries.loc[
        result.countries["convention_count"] >= threshold
    ].copy()
    country_metrics = st.columns(2)
    country_metrics[0].metric(
        "Conventions avec pays renseigné et non ambigu",
        (
            f"{_format_count(int(summary['country_denominator']))} / "
            f"{_format_count(int(summary['total_conventions']))}"
        ),
    )
    country_metrics[1].metric(
        "Conventions sans pays renseigné",
        _format_count(int(summary["missing_country_conventions"])),
    )
    if country_rows.empty:
        st.info("Aucun groupe par pays ne satisfait le seuil configuré.")
    else:
        country_rows["Pays"] = country_rows["country"].astype(str)
        country_rows["Conventions distinctes"] = country_rows[
            "convention_count"
        ].map(lambda value: _format_count(int(value)))
        country_rows["Dénominateur — pays renseignés/non ambigus"] = (
            country_rows["denominator"].map(
                lambda value: _format_count(int(value))
            )
        )
        country_rows["Part parmi les pays renseignés/non ambigus"] = (
            country_rows["percentage"].map(_format_percentage)
        )
        st.dataframe(
            country_rows[
                [
                    "Pays",
                    "Conventions distinctes",
                    "Dénominateur — pays renseignés/non ambigus",
                    "Part parmi les pays renseignés/non ambigus",
                ]
            ],
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Les pourcentages ont pour dénominateur les conventions avec un "
            "pays renseigné et non ambigu. Les valeurs absentes sont comptées "
            "séparément et ne sont assimilées ni à la France ni à l’étranger."
        )


def _render_quality_page(full_data: pd.DataFrame, filtered_data: pd.DataFrame) -> None:
    st.title("Qualité des données")
    st.caption(
        "Contrôles agrégés uniquement ; aucune correction n’est appliquée au classeur."
    )
    full_summary = quality_summary(full_data, QUALITY_FIELDS)

    global_metrics = st.columns(3)
    global_metrics[0].metric(
        "Lignes — fichier complet",
        _format_count(int(full_summary["row_count"])),
    )
    global_metrics[1].metric(
        "Conventions — fichier complet",
        _format_count(int(full_summary["convention_count"])),
    )
    global_metrics[2].metric(
        "Conventions — périmètre filtré",
        _format_count(count_conventions(filtered_data)),
    )
    st.caption(
        "Les deux premiers indicateurs concernent le fichier complet ; "
        "le troisième suit les filtres globaux."
    )

    available_fields = [
        field for field in QUALITY_FIELDS if field in full_data.columns
    ]
    missing_fields = full_summary["unavailable_fields"]
    if missing_fields:
        labels = [FIELD_LABELS.get(field, field) for field in missing_fields]
        st.warning(
            "Champs facultatifs absents ; les contrôles correspondants sont "
            f"indisponibles : {', '.join(labels)}."
        )
    if available_fields:
        full_coverage = field_coverage(full_data, available_fields)
        full_coverage["label"] = full_coverage["field"].map(
            FIELD_LABELS
        ).fillna(full_coverage["field"])
        st.subheader("Couverture — fichier complet")
        st.dataframe(
            _localized_coverage(full_data, available_fields),
            hide_index=True,
            width="stretch",
        )
        _render_plot(
            _bar_figure(
                full_coverage.sort_values(
                    "completion_percentage", ascending=True, kind="stable"
                ),
                "label",
                "completion_percentage",
                "Couverture des champs — fichier complet",
                "Valeurs renseignées (%)",
                horizontal=True,
                color="#557C9E",
            )
        )

    st.subheader("Couverture — périmètre filtré")
    if filtered_data.empty:
        st.info(
            "Aucune ligne ne correspond aux filtres ; "
            "la couverture filtrée n’est pas calculable."
        )
    else:
        filtered_fields = [
            field for field in QUALITY_FIELDS if field in filtered_data.columns
        ]
        st.dataframe(
            _localized_coverage(filtered_data, filtered_fields),
            hide_index=True,
            width="stretch",
        )

    if "annee_academique" in full_data.columns and available_fields:
        st.subheader("Couverture par année académique")
        selected_quality_fields = st.multiselect(
            "Champs à comparer",
            options=available_fields,
            default=[
                field
                for field in (
                    "nature_du_stage",
                    "entreprise",
                    "pays_lieu_stage",
                    "date_debut",
                )
                if field in available_fields
            ],
            format_func=lambda field: FIELD_LABELS.get(field, field),
        )
        if selected_quality_fields:
            yearly = yearly_field_coverage(
                full_data, "annee_academique", selected_quality_fields
            )
            yearly["Champ"] = yearly["field"].map(FIELD_LABELS).fillna(
                yearly["field"]
            )
            yearly = yearly.loc[yearly["completion_percentage"].notna()]
            yearly = _sort_year_categories(yearly, "academic_year")
            px = _plotly_express()
            if px is None:
                st.warning(PLOTLY_ERROR)
            elif not yearly.empty:
                figure = px.line(
                    yearly,
                    x="academic_year",
                    y="completion_percentage",
                    color="Champ",
                    markers=True,
                    title="Couverture des champs par année renseignée",
                    labels={
                        "academic_year": "Année académique",
                        "completion_percentage": "Valeurs renseignées (%)",
                    },
                    color_discrete_sequence=px.colors.qualitative.Safe,
                )
                figure.update_layout(template="plotly_white")
                _render_plot(figure)
                st.caption(
                    "Le libellé « Non renseigné » regroupe les lignes sans année "
                    "académique ; chaque taux a pour dénominateur les lignes de son année."
                )
        else:
            st.info("Sélectionnez au moins un champ pour afficher la comparaison.")

    st.subheader("Alertes de qualité")
    if "annee_academique" in full_data.columns:
        if full_data["annee_academique"].isna().any():
            st.warning("Des lignes n’ont pas d’année académique renseignée.")
        valid_years = [
            value
            for value in full_data["annee_academique"].dropna().unique()
            if isinstance(value, str)
        ]
        if valid_years:
            latest_year = max(valid_years, key=_academic_sort_key)
            st.warning(
                f"L’année la plus récente observée ({latest_year}) peut être "
                "incomplète ; aucune comparaison annuelle officielle n’est proposée."
            )
    if "nature_du_stage" in full_data.columns:
        missing_natures = int(full_data["nature_du_stage"].isna().sum())
        if missing_natures:
            st.warning(
                f"La nature du stage est absente sur "
                f"{_format_count(missing_natures)} ligne(s) du fichier complet."
            )
    if "pays_lieu_stage" not in full_data.columns:
        st.warning(
            "Le champ du pays du lieu de stage est absent ; "
            "l’analyse géographique est indisponible."
        )
    elif full_data["pays_lieu_stage"].isna().any():
        st.warning(
            "Le pays du lieu de stage est manquant sur une partie des lignes ; "
            "les destinations affichées ne représentent que les valeurs renseignées."
        )


def _load_source() -> pd.DataFrame:
    return load_stages(
        STAGES_SOURCE_FILE,
        required_columns=REQUIRED_APP_COLUMNS,
        optional_columns=OPTIONAL_SOURCE_COLUMNS,
    )


def main() -> None:
    st.set_page_config(
        page_title="Pilotage des stages — BI",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container {max-width: 1480px; padding-top: 1.5rem; padding-bottom: 3rem;}
        [data-testid="stMetric"] {border: 1px solid #D9E2F3; padding: 1rem; border-radius: .6rem; background: #FBFCFE;}
        h1, h2, h3 {color: #17365D;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.title("Pilotage des stages")
        st.caption("Tableau de bord Business Intelligence")
        page = st.radio("Navigation", options=PAGE_NAMES)
        st.divider()
        st.caption(
            "Les indicateurs de conventions ne sont pas assimilés au nombre de stages."
        )

    try:
        data = _load_source()
    except DataFileError as exc:
        st.error(f"Chargement impossible : {exc}")
        st.info(
            "Vérifiez la présence du classeur Excel autorisé dans `data/raw/` "
            "et son intégrité."
        )
        return
    except MissingColumnsError as exc:
        st.error(f"Schéma du classeur invalide : {exc}")
        st.info(
            "Les indicateurs dépendants des colonnes manquantes sont suspendus. "
            "Aucune valeur de remplacement n’est utilisée."
        )
        return

    st.title("Filtres globaux")
    filtered_data = _render_global_filters(data)
    st.caption(
        f"Périmètre sélectionné : {_format_count(len(filtered_data))} lignes · "
        f"{_format_count(count_conventions(filtered_data))} conventions distinctes."
    )
    st.caption(_active_filter_summary())
    st.divider()

    if page == "Vue d’ensemble":
        _render_overview(filtered_data)
    elif page == "Analyse temporelle":
        _render_temporal_analysis(filtered_data)
    elif page == "Analyse des stages":
        _render_stage_analysis(filtered_data)
    elif page == "Entreprises et géographie":
        _render_exploration_page(filtered_data)
    else:
        _render_quality_page(data, filtered_data)

    st.divider()
    st.caption(
        f"Source : {STAGES_SOURCE_FILE.name} · lecture seule · "
        "données individuelles non affichées · exports désactivés."
    )


if __name__ == "__main__":
    main()
