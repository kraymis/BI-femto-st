import { describe, expect, it } from 'vitest'
import { createFilterQuery } from './dashboardApi'
import type { FilterOptions, SelectedFilters } from '../types'

const options: FilterOptions = {
  academic_years: [
    { value: '2024/2025', label: '2024/2025', is_missing: false },
    { value: null, label: 'Non renseigné', is_missing: true },
  ],
  stage_types: [
    { value: 'PFE', label: 'PFE', is_missing: false },
    { value: 'SIB', label: 'SIB', is_missing: false },
  ],
  stage_natures: [
    { value: 'Entreprise', label: 'Entreprise', is_missing: false },
  ],
}

describe('createFilterQuery', () => {
  it('encodes repeated selections and explicit missing-value flags', () => {
    const selected: SelectedFilters = {
      academic_years: ['value:2024/2025', 'missing:'],
      stage_types: ['value:PFE', 'value:SIB'],
      stage_natures: ['value:Entreprise'],
    }

    const query = new URLSearchParams(createFilterQuery(options, selected))

    expect(query.getAll('academic_years')).toEqual(['2024/2025'])
    expect(query.get('include_missing_year')).toBe('true')
    expect(query.getAll('stage_types')).toEqual(['PFE', 'SIB'])
    expect(query.get('include_missing_type')).toBe('false')
    expect(query.getAll('stage_natures')).toEqual(['Entreprise'])
    expect(query.get('include_missing_nature')).toBe('false')
  })

  it('serializes an empty selection instead of dropping its filter', () => {
    const selected: SelectedFilters = {
      academic_years: [],
      stage_types: [],
      stage_natures: [],
    }

    const query = new URLSearchParams(createFilterQuery(options, selected))

    expect(query.getAll('academic_years')).toEqual([])
    expect(query.getAll('stage_types')).toEqual([])
    expect(query.getAll('stage_natures')).toEqual([])
    expect(query.get('include_missing_year')).toBe('false')
    expect(query.get('include_missing_type')).toBe('false')
    expect(query.get('include_missing_nature')).toBe('false')
  })
})
