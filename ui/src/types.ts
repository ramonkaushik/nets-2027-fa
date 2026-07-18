export interface Player {
  id: number
  name: string
  position: string | null
  salary: number | null
  years_left: number | null
  option_type: string | null
  gp: number | null
  mpg: number | null
  pts: number | null
  reb: number | null
  ast: number | null
  stl: number | null
  blk: number | null
  tov: number | null
  ts_pct: number | null
  efg_pct: number | null
  usg_pct: number | null
  bpm: number | null
  vorp: number | null
  per: number | null
  pts_per_75: number | null
  e_off_rating: number | null
  e_def_rating: number | null
  e_net_rating: number | null
}

export interface FreeAgent extends Player {
  prior_team: string | null
  fa_type: string | null
}

export interface CapSummary {
  season: string
  salary_cap: number
  tax_line: number
  first_apron: number
  second_apron: number
  committed: number
  expiring: number
  projected_next: number
  space_vs_cap: number
  room_to_tax: number
  room_to_apron1: number
  room_to_apron2: number
}
