#!/usr/bin/env python3
"""
Golf Playbooks — Navigation Patch & Tier Distribution Builder
==============================================================
Generates clean per-tier distribution folders from a single source.

Usage
-----
  # Build all three tiers at once:
  python3 patch_playbooks.py --tier standard --out dist/standard
  python3 patch_playbooks.py --tier pro      --out dist/pro
  python3 patch_playbooks.py --tier elite    --out dist/elite

  # Or patch in-place (no --out) — default tier is standard:
  python3 patch_playbooks.py

What it does per file
---------------------
  1. Injects a TIER constant + DOM-removal init block into every HTML file.
     TIER = 'standard' | 'pro' | 'elite' — controls which data-tier elements render.
  2. Adds a "⌂ All Playbooks" home nav bar at the very top.
  3. Adds a "Related Playbooks" panel at the very bottom.
  4. Excludes Pro-only guides from the Standard build.
  5. Excludes Elite-only guides from Standard and Pro builds.
  6. Copies index_pro.html  → index.html in the Pro output folder.
  7. Copies index_elite.html → index.html in the Elite output folder.
  8. Copies non-HTML assets (sw.js, manifest.json, icons/) automatically.

Tier gating in HTML source files
---------------------------------
  Advanced Pro tabs/sections carry:      data-tier="pro"
  Advanced Elite tabs/sections carry:    data-tier="elite"

  The injected TIER script removes elements that exceed the buyer's tier:
    - Standard build:  removes data-tier="pro" AND data-tier="elite"
    - Pro build:       removes data-tier="elite" only
    - Elite build:     removes nothing — all content visible

Safe to re-run — existing tier markers are detected and replaced cleanly.
"""

# <!-- version:v3.7 · 2026-06-13 · patch_playbooks.py — guides 56–57 added (US & European Competitive Pathway); 45 Standard guides total -->

import os, re, shutil, argparse

# ── Guide registry ────────────────────────────────────────────────────────
# filename → (display title, emoji, accent colour)
GUIDES = {
    # ── Core guides (Standard + Pro + Elite) ──────────────────────────────
    '01_putting_pro.html':              ('Putting Playbook',              '🎯', '#e8b800'),
    '02_shortgame_pro.html':            ('Short Game Playbook',           '🌊', '#2ec4b6'),
    '03_longgame_pro.html':             ('Long Game Playbook',            '🏌️', '#5ecb3e'),
    '04_complete_golfer.html':          ('The Complete Golfer',           '🧭', '#ff6b35'),
    '05_pre_shot_routine.html':         ('Pre-Shot Routine',              '🔁', '#5ecb3e'),
    '06_golf_fitness.html':             ('Golf Fitness Plan',             '💪', '#ff6b35'),
    '07_golf_nutrition.html':           ('Golf Nutrition Plan',           '🍎', '#5ecb3e'),
    '08_pro_round_prep.html':           ('Pro Round Prep',                '🗺️', '#e8b800'),
    '09_golf_coach_ai.html':            ('Golf Coach AI',                 '🤖', '#5ecb3e'),
    '10_scratch_plan.html':             ('Your Milestone Plan',           '🏆', '#e8b800'),
    '11_shot_dispersion.html':          ('Shot Dispersion Mapping',       '📊', '#5ecb3e'),
    '12_rules_of_golf.html':            ('Rules of Golf',                 '📜', '#e8b800'),
    '13_injury_prevention.html':        ('Injury Prevention',             '🩺', '#ff6b35'),
    '14_video_analysis.html':           ('Video Analysis',                '🎥', '#2ec4b6'),
    '15_equipment_fitting.html':        ('Equipment Fitting',             '🔧', '#e8b800'),
    '16_solo_pressure_round.html':      ('Solo Pressure Round',           '🔥', '#ff6b35'),
    '17_progress_journal.html':         ('Progress Journal',              '📓', '#9b72f5'),
    '18_training_aids_2.html':          ('Training Arsenal',              '🛠️', '#5ecb3e'),
    '20_course_management.html':        ('Course Management',             '⚖️', '#e8b800'),
    '21_mental_game.html':              ('Mental Game Mastery',           '🧘', '#9b72f5'),
    '22_wedge_distances.html':          ('Wedge Distance Matrix',         '📏', '#e8b800'),
    '23_weather_conditions.html':       ('Weather & Conditions',          '🌬️', '#2ec4b6'),
    '24_competitive_strategy.html':     ('Competitive Strategy',          '🏆', '#e8b800'),
    '25_speed_training.html':           ('Speed Training',                '⚡', '#5ecb3e'),
    '26_stats_interpretation.html':     ('Stats & SG Interpretation',     '🔢', '#2ec4b6'),
    '27_six_month_plan.html':           ('Months 1–6 Plan',               '📅', '#e8b800'),
    '28_months_7_12_plan.html':         ('Months 7–12 Plan',              '📆', '#e8b800'),
    '29_months_13_18_plan.html':        ('Months 13–18 Plan',             '🎯', '#c8921a'),
    '30_months_19_24_plan.html':        ('Months 19–24 Plan',             '🏆', '#3a8a3a'),
    'caddie_card.html':                 ('Caddie Reference Card',         '📋', '#2ec4b6'),
    'swing_mechanics.html':             ('Swing Mechanics',               '⚙️', '#5ecb3e'),
    'golf_analysis.html':               ('Launch Monitor Analysis',       '📈', '#2ec4b6'),
    'practice_plan.html':               ('4-Week Programme',              '🗓️', '#2ec4b6'),
    'mevo_gen2_playbook.html':          ('Mevo Gen2 Data Mastery',        '📡', '#2ec4b6'),
    'hackmotion_playbook.html':         ('HackMotion Data Mastery',       '🖥️', '#2ec4b6'),
    'golf_weekly_dashboard.html':       ('Weekly Practice Dashboard',     '📅', '#5ecb3e'),
    'motivation.html':                  ('The Honest Case for Scratch',   '🔥', '#a0c850'),
    'on_course_reference_A5_8pp.html':  ('On-Course Reference A5',        '📄', '#48b0a8'),
    'tracking_app.html':                ('Performance Tracker v1',        '📊', '#2ec4b6'),
    'tracking_app_v2.html':             ('Performance Tracker',           '📊', '#5ecb3e'),
    '31_on_course_notes.html':          ('On-Course Notes',               '🗺️', '#5ecb3e'),
    '32_putting_green_reading.html':    ('Green Reading Deep Dive',       '📐', '#5ecb3e'),
    '33_competitive_pathway.html':      ('Competitive Pathway',           '🏆', '#5ecb3e'),
    '34_coaching_relationship.html':    ('The Coaching Relationship',     '🎓', '#2ec4b6'),
    '35_links_travel_golf.html':        ('Course Types & Travel Golf',    '🌊', '#5ecb3e'),
    '36_playing_partners.html':         ('Playing Partners',              '🤝', '#2ec4b6'),
    '37_approach_zone.html':            ('The 100–175 Yard Zone',         '🎯', '#e8b800'),
    # ── Pro-only guides (Pro + Elite) ────────────────────────────────────
    '38_practice_structure.html':       ('Practice Structure Science',    '🧬', '#c8d870'),
    '39_ground_reaction_force.html':    ('Ground Reaction Force',         '⚡', '#c8d870'),
    '40_decision_architecture.html':    ('Decision Architecture & EV',    '🎲', '#c8d870'),
    # ── Elite-only guides ────────────────────────────────────────────────
    '41_plus_hcp_sg_targets.html':      ('Plus-HCP SG Targets',           '⭐', '#c8d8e8'),
    '42_national_amateur_circuit.html': ('National Amateur Circuit',      '🏆', '#c8d8e8'),
    '43_caddie_preparation.html':       ('Caddie Prep & Yardage Books',   '📖', '#c8d8e8'),
    '44_golfmetrics_deepdive.html':     ('Golfmetrics Deep-Dive',         '🔬', '#c8d8e8'),
    '45_sportsbox_ai.html':             ('Sportsbox AI Integration',      '🎬', '#c8d8e8'),
    '46_county_team_golf.html':         ('County Team & Rep Golf',        '🏅', '#c8d8e8'),
    '47_elite_performance_psychology.html': ('Elite Performance Psychology', '🧠', '#c8d8e8'),
    '48_elite_physical_performance.html':   ('Elite Physical Performance',   '💪', '#c8d8e8'),
    '49_advanced_game_construction.html':   ('Advanced Game Construction',   '🎯', '#c8d8e8'),
    # ── New global expansion guides (added v3.4) ──────────────────────────
    '50_links_golf_strategy.html':          ('Links Golf Strategy',           '🌬️', '#2ec4b6'),
    '51_gap_zone_mastery.html':             ('Gap Zone Mastery',              '📏', '#e8b800'),
    '52_matchplay_formats.html':            ('Matchplay Format Strategies',   '🤝', '#a0c850'),
    '53_aimpoint_express.html':             ('AimPoint Express',               '☝️', '#48b0a8'),
    '54_ai_swing_analysis.html':            ('AI Swing Analysis Tools',        '🤖', '#e0b840'),
    '55_launch_monitor_fitting.html':       ('Launch Monitor Fitting',         '📊', '#c0e060'),
    '56_us_competitive_pathway.html':       ('US Competitive Pathway',         '🇺🇸', '#48b0a8'),
    '57_european_competitive_pathway.html': ('European Competitive Pathway',   '🇪🇺', '#a0c850'),
    # ── Elite+ guides (EP series) ─────────────────────────────────────────
    'ep1_season_decision_architecture.html':    ('Season Decision Architecture',  '🗓️', '#c8d8e8'),
    'ep2_multiseason_sg_analytics.html':        ('Multi-Season SG Analytics',     '📈', '#c8d8e8'),
    'ep3_identity_mental_game.html':            ('Identity & Mental Game',        '🧠', '#c8d8e8'),
    'ep4_proximity_approach_mastery.html':      ('Proximity & Approach Mastery',  '🎯', '#c8d8e8'),
    'ep5_movement_screening_fitness.html':      ('Movement Screening & Fitness',  '💪', '#c8d8e8'),
    'ep6_dynamic_replanning.html':              ('Dynamic Replanning',            '🔄', '#c8d8e8'),
    'ep7_complete_wedge_system.html':           ('Complete Wedge System',         '🏌️', '#c8d8e8'),
    'ep8_arccos_air_mastery.html':              ('Arccos Air Mastery',            '📡', '#c8d8e8'),
    'ep9_winter_training_offseason.html':       ('Winter Training & Off-Season',  '❄️', '#c8d8e8'),
    'ep10_world_handicap_system.html':          ('WHS Strategic Understanding',   '📊', '#c8d8e8'),
    'ep11_advanced_coaching_relationship.html': ('Advanced Coaching Relationship','🎓', '#c8d8e8'),
}

# ── Related guides map ────────────────────────────────────────────────────
# filename → [related filenames in priority order, max 5]
RELATED = {
    '01_putting_pro.html':              ['02_shortgame_pro.html','18_training_aids_2.html','05_pre_shot_routine.html','17_progress_journal.html','09_golf_coach_ai.html'],
    '02_shortgame_pro.html':            ['01_putting_pro.html','22_wedge_distances.html','18_training_aids_2.html','05_pre_shot_routine.html','15_equipment_fitting.html'],
    '03_longgame_pro.html':             ['swing_mechanics.html','11_shot_dispersion.html','25_speed_training.html','14_video_analysis.html','39_ground_reaction_force.html'],
    '04_complete_golfer.html':          ['10_scratch_plan.html','21_mental_game.html','05_pre_shot_routine.html','17_progress_journal.html','26_stats_interpretation.html'],
    '05_pre_shot_routine.html':         ['21_mental_game.html','16_solo_pressure_round.html','08_pro_round_prep.html','04_complete_golfer.html'],
    '06_golf_fitness.html':             ['25_speed_training.html','07_golf_nutrition.html','13_injury_prevention.html','10_scratch_plan.html'],
    '07_golf_nutrition.html':           ['06_golf_fitness.html','08_pro_round_prep.html','13_injury_prevention.html','10_scratch_plan.html'],
    '08_pro_round_prep.html':           ['05_pre_shot_routine.html','20_course_management.html','07_golf_nutrition.html','21_mental_game.html','43_caddie_preparation.html'],
    '09_golf_coach_ai.html':            ['26_stats_interpretation.html','mevo_gen2_playbook.html','hackmotion_playbook.html','17_progress_journal.html'],
    '10_scratch_plan.html':             ['27_six_month_plan.html','28_months_7_12_plan.html','29_months_13_18_plan.html','30_months_19_24_plan.html','17_progress_journal.html'],
    '11_shot_dispersion.html':          ['03_longgame_pro.html','mevo_gen2_playbook.html','20_course_management.html','09_golf_coach_ai.html'],
    '12_rules_of_golf.html':            ['08_pro_round_prep.html','24_competitive_strategy.html','16_solo_pressure_round.html'],
    '13_injury_prevention.html':        ['06_golf_fitness.html','25_speed_training.html','07_golf_nutrition.html'],
    '14_video_analysis.html':           ['54_ai_swing_analysis.html','swing_mechanics.html','03_longgame_pro.html','hackmotion_playbook.html','09_golf_coach_ai.html'],
    '15_equipment_fitting.html':        ['55_launch_monitor_fitting.html','01_putting_pro.html','mevo_gen2_playbook.html','11_shot_dispersion.html','45_sportsbox_ai.html'],
    '16_solo_pressure_round.html':      ['21_mental_game.html','05_pre_shot_routine.html','24_competitive_strategy.html','17_progress_journal.html'],
    '17_progress_journal.html':         ['26_stats_interpretation.html','09_golf_coach_ai.html','10_scratch_plan.html','16_solo_pressure_round.html'],
    '18_training_aids_2.html':          ['mevo_gen2_playbook.html','hackmotion_playbook.html','01_putting_pro.html','02_shortgame_pro.html','38_practice_structure.html'],
    '20_course_management.html':        ['08_pro_round_prep.html','11_shot_dispersion.html','24_competitive_strategy.html','40_decision_architecture.html'],
    '21_mental_game.html':              ['05_pre_shot_routine.html','16_solo_pressure_round.html','08_pro_round_prep.html','24_competitive_strategy.html','42_national_amateur_circuit.html'],
    '22_wedge_distances.html':          ['02_shortgame_pro.html','mevo_gen2_playbook.html','11_shot_dispersion.html'],
    '23_weather_conditions.html':       ['20_course_management.html','08_pro_round_prep.html','03_longgame_pro.html'],
    '24_competitive_strategy.html':     ['52_matchplay_formats.html','21_mental_game.html','12_rules_of_golf.html','16_solo_pressure_round.html','40_decision_architecture.html'],
    '25_speed_training.html':           ['06_golf_fitness.html','03_longgame_pro.html','mevo_gen2_playbook.html','13_injury_prevention.html'],
    '26_stats_interpretation.html':     ['09_golf_coach_ai.html','mevo_gen2_playbook.html','17_progress_journal.html','41_plus_hcp_sg_targets.html','44_golfmetrics_deepdive.html'],
    '27_six_month_plan.html':           ['10_scratch_plan.html','28_months_7_12_plan.html','29_months_13_18_plan.html','30_months_19_24_plan.html'],
    '28_months_7_12_plan.html':         ['10_scratch_plan.html','27_six_month_plan.html','29_months_13_18_plan.html','30_months_19_24_plan.html'],
    '29_months_13_18_plan.html':        ['10_scratch_plan.html','28_months_7_12_plan.html','30_months_19_24_plan.html','24_competitive_strategy.html','17_progress_journal.html'],
    '30_months_19_24_plan.html':        ['10_scratch_plan.html','29_months_13_18_plan.html','24_competitive_strategy.html','17_progress_journal.html','21_mental_game.html'],
    'caddie_card.html':                 ['22_wedge_distances.html','23_weather_conditions.html','11_shot_dispersion.html','20_course_management.html'],
    'swing_mechanics.html':             ['03_longgame_pro.html','14_video_analysis.html','hackmotion_playbook.html','mevo_gen2_playbook.html'],
    'golf_analysis.html':               ['09_golf_coach_ai.html','mevo_gen2_playbook.html','11_shot_dispersion.html','10_scratch_plan.html'],
    'practice_plan.html':               ['10_scratch_plan.html','27_six_month_plan.html','18_training_aids_2.html','17_progress_journal.html'],
    'mevo_gen2_playbook.html':          ['hackmotion_playbook.html','09_golf_coach_ai.html','11_shot_dispersion.html','26_stats_interpretation.html'],
    'hackmotion_playbook.html':         ['mevo_gen2_playbook.html','09_golf_coach_ai.html','swing_mechanics.html','14_video_analysis.html','45_sportsbox_ai.html'],
    'golf_weekly_dashboard.html':       ['tracking_app_v2.html','17_progress_journal.html','26_stats_interpretation.html','10_scratch_plan.html'],
    'motivation.html':                  ['10_scratch_plan.html','04_complete_golfer.html','27_six_month_plan.html','21_mental_game.html'],
    'on_course_reference_A5_8pp.html':  ['caddie_card.html','22_wedge_distances.html','23_weather_conditions.html','20_course_management.html'],
    'tracking_app.html':                ['tracking_app_v2.html','17_progress_journal.html','26_stats_interpretation.html','09_golf_coach_ai.html'],
    'tracking_app_v2.html':             ['17_progress_journal.html','26_stats_interpretation.html','09_golf_coach_ai.html','10_scratch_plan.html'],
    '31_on_course_notes.html':          ['20_course_management.html','08_pro_round_prep.html','caddie_card.html','17_progress_journal.html','26_stats_interpretation.html'],
    '32_putting_green_reading.html':    ['53_aimpoint_express.html','01_putting_pro.html','31_on_course_notes.html','23_weather_conditions.html','caddie_card.html'],
    '33_competitive_pathway.html':      ['56_us_competitive_pathway.html','57_european_competitive_pathway.html','24_competitive_strategy.html','21_mental_game.html','42_national_amateur_circuit.html'],
    '34_coaching_relationship.html':    ['09_golf_coach_ai.html','14_video_analysis.html','mevo_gen2_playbook.html','17_progress_journal.html','hackmotion_playbook.html'],
    '35_links_travel_golf.html':        ['50_links_golf_strategy.html','23_weather_conditions.html','20_course_management.html','02_shortgame_pro.html','caddie_card.html'],
    '36_playing_partners.html':         ['21_mental_game.html','05_pre_shot_routine.html','24_competitive_strategy.html','33_competitive_pathway.html'],
    '37_approach_zone.html':            ['51_gap_zone_mastery.html','03_longgame_pro.html','22_wedge_distances.html','20_course_management.html','mevo_gen2_playbook.html'],
    # ── New Standard guides (50–55) ─────────────────────────────────────
    '50_links_golf_strategy.html':      ['35_links_travel_golf.html','23_weather_conditions.html','20_course_management.html','02_shortgame_pro.html','caddie_card.html'],
    '51_gap_zone_mastery.html':         ['37_approach_zone.html','22_wedge_distances.html','mevo_gen2_playbook.html','55_launch_monitor_fitting.html','38_practice_structure.html'],
    '52_matchplay_formats.html':        ['24_competitive_strategy.html','33_competitive_pathway.html','21_mental_game.html','16_solo_pressure_round.html','46_county_team_golf.html'],
    '53_aimpoint_express.html':         ['01_putting_pro.html','32_putting_green_reading.html','05_pre_shot_routine.html','18_training_aids_2.html'],
    '54_ai_swing_analysis.html':        ['14_video_analysis.html','hackmotion_playbook.html','45_sportsbox_ai.html','swing_mechanics.html','mevo_gen2_playbook.html'],
    '55_launch_monitor_fitting.html':   ['15_equipment_fitting.html','mevo_gen2_playbook.html','11_shot_dispersion.html','51_gap_zone_mastery.html','37_approach_zone.html'],
    '56_us_competitive_pathway.html':   ['33_competitive_pathway.html','57_european_competitive_pathway.html','24_competitive_strategy.html','42_national_amateur_circuit.html','12_rules_of_golf.html'],
    '57_european_competitive_pathway.html': ['33_competitive_pathway.html','56_us_competitive_pathway.html','50_links_golf_strategy.html','35_links_travel_golf.html','42_national_amateur_circuit.html'],
    # ── Pro-only guides ───────────────────────────────────────────────────
    '38_practice_structure.html':       ['05_pre_shot_routine.html','26_stats_interpretation.html','18_training_aids_2.html','17_progress_journal.html'],
    '39_ground_reaction_force.html':    ['03_longgame_pro.html','06_golf_fitness.html','25_speed_training.html','mevo_gen2_playbook.html'],
    '40_decision_architecture.html':    ['20_course_management.html','11_shot_dispersion.html','26_stats_interpretation.html','24_competitive_strategy.html'],
    # ── Elite-only guides ────────────────────────────────────────────────
    '41_plus_hcp_sg_targets.html':      ['26_stats_interpretation.html','44_golfmetrics_deepdive.html','42_national_amateur_circuit.html','17_progress_journal.html','09_golf_coach_ai.html'],
    '42_national_amateur_circuit.html': ['33_competitive_pathway.html','57_european_competitive_pathway.html','43_caddie_preparation.html','21_mental_game.html','41_plus_hcp_sg_targets.html'],
    '43_caddie_preparation.html':       ['08_pro_round_prep.html','42_national_amateur_circuit.html','22_wedge_distances.html','23_weather_conditions.html','20_course_management.html'],
    '44_golfmetrics_deepdive.html':     ['26_stats_interpretation.html','41_plus_hcp_sg_targets.html','17_progress_journal.html','09_golf_coach_ai.html','mevo_gen2_playbook.html'],
    '45_sportsbox_ai.html':             ['hackmotion_playbook.html','14_video_analysis.html','34_coaching_relationship.html','mevo_gen2_playbook.html','38_practice_structure.html'],
    '46_county_team_golf.html':         ['33_competitive_pathway.html','42_national_amateur_circuit.html','21_mental_game.html','24_competitive_strategy.html','08_pro_round_prep.html'],
    '47_elite_performance_psychology.html': ['21_mental_game.html','16_solo_pressure_round.html','05_pre_shot_routine.html','42_national_amateur_circuit.html','48_elite_physical_performance.html'],
    '48_elite_physical_performance.html':   ['06_golf_fitness.html','25_speed_training.html','07_golf_nutrition.html','47_elite_performance_psychology.html','13_injury_prevention.html'],
    '49_advanced_game_construction.html':   ['20_course_management.html','40_decision_architecture.html','41_plus_hcp_sg_targets.html','43_caddie_preparation.html','22_wedge_distances.html'],
    # ── Elite+ RELATED ────────────────────────────────────────────────────
    'ep1_season_decision_architecture.html':    ['40_decision_architecture.html','33_competitive_pathway.html','42_national_amateur_circuit.html','24_competitive_strategy.html','ep6_dynamic_replanning.html'],
    'ep2_multiseason_sg_analytics.html':        ['26_stats_interpretation.html','41_plus_hcp_sg_targets.html','44_golfmetrics_deepdive.html','17_progress_journal.html','ep6_dynamic_replanning.html'],
    'ep3_identity_mental_game.html':            ['47_elite_performance_psychology.html','21_mental_game.html','16_solo_pressure_round.html','05_pre_shot_routine.html','ep1_season_decision_architecture.html'],
    'ep4_proximity_approach_mastery.html':      ['37_approach_zone.html','41_plus_hcp_sg_targets.html','26_stats_interpretation.html','mevo_gen2_playbook.html','ep2_multiseason_sg_analytics.html'],
    'ep5_movement_screening_fitness.html':      ['48_elite_physical_performance.html','06_golf_fitness.html','13_injury_prevention.html','25_speed_training.html','ep9_winter_training_offseason.html'],
    'ep6_dynamic_replanning.html':              ['10_scratch_plan.html','26_stats_interpretation.html','34_coaching_relationship.html','ep2_multiseason_sg_analytics.html','ep11_advanced_coaching_relationship.html'],
    'ep7_complete_wedge_system.html':           ['02_shortgame_pro.html','22_wedge_distances.html','37_approach_zone.html','mevo_gen2_playbook.html','ep4_proximity_approach_mastery.html'],
    'ep8_arccos_air_mastery.html':              ['26_stats_interpretation.html','44_golfmetrics_deepdive.html','ep2_multiseason_sg_analytics.html','41_plus_hcp_sg_targets.html','17_progress_journal.html'],
    'ep9_winter_training_offseason.html':       ['06_golf_fitness.html','25_speed_training.html','ep5_movement_screening_fitness.html','48_elite_physical_performance.html','10_scratch_plan.html'],
    'ep10_world_handicap_system.html':          ['33_competitive_pathway.html','42_national_amateur_circuit.html','17_progress_journal.html','ep1_season_decision_architecture.html','ep6_dynamic_replanning.html'],
    'ep11_advanced_coaching_relationship.html': ['34_coaching_relationship.html','45_sportsbox_ai.html','ep6_dynamic_replanning.html','14_video_analysis.html','ep2_multiseason_sg_analytics.html'],
}

# ── Tier membership sets ──────────────────────────────────────────────────
# Files that only appear in Pro and Elite builds (excluded from Standard)
PRO_ONLY_FILES = {
    '38_practice_structure.html',
    '39_ground_reaction_force.html',
    '40_decision_architecture.html',
    'index_pro.html',
    'index_elite.html',
}

# Files that only appear in the Elite build
ELITE_ONLY_FILES = {
    '41_plus_hcp_sg_targets.html',
    '42_national_amateur_circuit.html',
    '43_caddie_preparation.html',
    '44_golfmetrics_deepdive.html',
    '45_sportsbox_ai.html',
    '46_county_team_golf.html',
    '47_elite_performance_psychology.html',
    '48_elite_physical_performance.html',
    '49_advanced_game_construction.html',
    'index_elite.html',
    # Elite+ series
    'ep1_season_decision_architecture.html',
    'ep2_multiseason_sg_analytics.html',
    'ep3_identity_mental_game.html',
    'ep4_proximity_approach_mastery.html',
    'ep5_movement_screening_fitness.html',
    'ep6_dynamic_replanning.html',
    'ep7_complete_wedge_system.html',
    'ep8_arccos_air_mastery.html',
    'ep9_winter_training_offseason.html',
    'ep10_world_handicap_system.html',
    'ep11_advanced_coaching_relationship.html',
}

# Files that use the paper/ink design (not the dark green theme)
PAPER_THEME = {
    '10_scratch_plan.html',
    '27_six_month_plan.html',
    '28_months_7_12_plan.html',
    '29_months_13_18_plan.html',
    '30_months_19_24_plan.html',
}

# Files to skip entirely in all builds (internal tools, legal, marketing assets)
SKIP = {
    'index.html', 'index_pro.html', 'index_elite.html',
    # Internal / marketing files — not part of any tier product
    'commercialisation_plan.html',
    'commercialisation_master.html',
    'elite_tier_brief.html',
    'landing.html',
    'privacy.html',
    'terms.html',
    'motivation.html',
}

# Non-HTML assets to copy into every dist folder
ASSET_FILES = {'sw.js', 'manifest.json'}
ASSET_DIRS  = {'icons'}


# ── Tier script injection ─────────────────────────────────────────────────

TIER_MARKER = '/* tier-init */'

def make_tier_script(tier: str) -> str:
    """
    Returns the inline <script> block that controls tier rendering.

    Logic:
      - Standard: removes data-tier="pro" AND data-tier="elite"
      - Pro:      removes data-tier="elite" only
      - Elite:    removes nothing — all content visible

    Elements marked data-tier="pro" carry pro-active visual marker in pro/elite.
    Elements marked data-tier="elite" carry elite-active visual marker in elite.
    """
    return (
        '<script>\n'
        f'/* tier-init */\n'
        f"const TIER = '{tier}'; // 'standard' | 'pro' | 'elite' — set by patch_playbooks.py\n"
        '(function() {\n'
        '  document.addEventListener(\'DOMContentLoaded\', function() {\n'
        '    document.querySelectorAll(\'[data-tier]\').forEach(function(el) {\n'
        '      var t = el.getAttribute(\'data-tier\');\n'
        '      if (t === \'pro\'   && TIER === \'standard\') { el.remove(); return; }\n'
        '      if (t === \'elite\' && TIER !== \'elite\')    { el.remove(); return; }\n'
        '      // Element is visible for this tier — mark it active for styling\n'
        '      el.setAttribute(\'data-tier-active\', t);\n'
        '    });\n'
        '  });\n'
        '})();\n'
        '</script>'
    )


def inject_tier(html: str, tier: str) -> str:
    """
    Injects or replaces the TIER constant script block in an HTML file.
    If a tier-init block already exists it is replaced in-place.
    Otherwise the new block is inserted immediately before </head>.
    """
    new_script = make_tier_script(tier)

    # Replace existing tier-init block (handles re-runs and tier changes)
    existing = re.search(
        r'<script>\s*/\* tier-init \*/.*?</script>',
        html, re.DOTALL
    )
    if existing:
        return html[:existing.start()] + new_script + html[existing.end():]

    # First injection — insert before </head>
    if '</head>' in html:
        return html.replace('</head>', new_script + '\n</head>', 1)

    # Fallback — insert before </body>
    return html.replace('</body>', new_script + '\n</body>', 1)


# ── Home nav bar ──────────────────────────────────────────────────────────

def make_home_nav(is_paper: bool) -> str:
    if is_paper:
        bg     = '#3d2e1a'
        border = 'rgba(26,18,8,0.3)'
        text   = 'rgba(245,239,228,0.55)'
        sub    = 'rgba(245,239,228,0.2)'
    else:
        bg     = '#111e11'
        border = 'rgba(160,200,80,0.2)'
        text   = 'rgba(232,240,216,0.55)'
        sub    = 'rgba(232,240,216,0.2)'
    return (
        '<!-- HOME NAV -->\n'
        f'<div style="background:{bg};border-bottom:1px solid {border};padding:10px 20px;'
        'display:flex;align-items:center;justify-content:space-between;'
        'position:relative;z-index:200;">\n'
        f'  <a href="index.html" style="font-family:\'Courier New\',monospace;font-size:10px;'
        f'letter-spacing:0.22em;text-transform:uppercase;color:{text};text-decoration:none;'
        'display:inline-flex;align-items:center;gap:8px;">\n'
        '    <span style="font-size:14px;line-height:1;">&#8962;</span> All Playbooks\n'
        '  </a>\n'
        f'  <span style="font-family:\'Courier New\',monospace;font-size:9px;'
        f'letter-spacing:0.18em;text-transform:uppercase;color:{sub};">The Scratch Project</span>\n'
        '</div>\n'
    )


# ── Related guides panel ──────────────────────────────────────────────────

def make_related_panel(filename: str, is_paper: bool, tier: str) -> str:
    """
    Builds the Related Playbooks panel for a given file.
    Filters out related guides that aren't available in the current tier.
    """
    rels_raw = RELATED.get(filename, [])
    if not rels_raw:
        return ''

    # Filter related guides to only those present in this tier's build
    def guide_in_tier(fname: str) -> bool:
        if fname in ELITE_ONLY_FILES:
            return tier == 'elite'
        if fname in PRO_ONLY_FILES:
            return tier in ('pro', 'elite')
        return True

    rels = [r for r in rels_raw if r in GUIDES and guide_in_tier(r)]
    if not rels:
        return ''

    if is_paper:
        outer_bg   = '#ede5d4'
        outer_bdr  = 'rgba(26,18,8,0.12)'
        label_col  = '#b54a22'
        card_bg    = '#f5efe4'
        card_bdr   = 'rgba(26,18,8,0.12)'
        card_text  = '#1a1208'
        footer_col = 'rgba(26,18,8,0.32)'
        font_body  = "'Libre Baskerville',Georgia,serif"
        font_mono  = "'Courier Prime','Courier New',monospace"
    else:
        outer_bg   = '#0d180d'
        outer_bdr  = 'rgba(160,200,80,0.15)'
        label_col  = 'rgba(160,200,80,0.75)'
        card_bg    = 'rgba(255,255,255,0.04)'
        card_bdr   = 'rgba(255,255,255,0.1)'
        card_text  = '#e8f0d8'
        footer_col = 'rgba(232,240,216,0.3)'
        font_body  = "'Inter',sans-serif"
        font_mono  = "'Courier New',monospace"

    cards_html = ''
    for r in rels:
        title, emoji, colour = GUIDES[r]
        cards_html += (
            f'    <a href="{r}" style="display:flex;align-items:center;gap:12px;'
            f'background:{card_bg};border:1px solid {card_bdr};border-radius:10px;'
            'padding:12px 14px;text-decoration:none;color:inherit;'
            'transition:border-color 0.2s;flex:1;min-width:150px;max-width:230px;">\n'
            f'      <span style="font-size:1.3rem;flex-shrink:0;">{emoji}</span>\n'
            f'      <span style="font-family:{font_body};font-size:12.5px;font-weight:600;'
            f'color:{card_text};line-height:1.35;">{title}</span>\n'
            '    </a>\n'
        )

    return (
        '\n<!-- RELATED GUIDES PANEL -->\n'
        f'<div style="background:{outer_bg};border-top:1px solid {outer_bdr};'
        'padding:28px 20px 36px;position:relative;z-index:1;">\n'
        f'  <p style="font-family:{font_mono};font-size:9px;letter-spacing:0.25em;'
        f'text-transform:uppercase;color:{label_col};margin-bottom:16px;">Related Playbooks</p>\n'
        '  <div style="display:flex;flex-wrap:wrap;gap:10px;">\n'
        f'{cards_html}'
        '  </div>\n'
        f'  <div style="margin-top:20px;padding-top:16px;border-top:1px solid {outer_bdr};text-align:center;">\n'
        f'    <a href="index.html" style="font-family:{font_mono};font-size:9px;'
        f'letter-spacing:0.2em;text-transform:uppercase;color:{footer_col};text-decoration:none;">'
        '&#8962; All Playbooks &#8212; Home</a>\n'
        '  </div>\n'
        '</div>\n'
    )


# ── Per-file patch ────────────────────────────────────────────────────────

def patch_file(src_path: str, dst_path: str, tier: str) -> str:
    """
    Reads src_path, applies all patches, writes to dst_path.
    Returns 'patched' or 'copied' (no changes needed).
    """
    fname    = os.path.basename(src_path)
    is_paper = fname in PAPER_THEME

    with open(src_path, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()

    changed = False

    # 1. Inject / update TIER script
    new_html = inject_tier(html, tier)
    if new_html != html:
        html    = new_html
        changed = True

    # 2. Add home nav bar (after <body>) if not already present
    if 'All Playbooks' not in html and '<!-- HOME NAV -->' not in html:
        nav = make_home_nav(is_paper)
        new_html = html.replace('<body>\n', '<body>\n' + nav, 1)
        if new_html == html:
            new_html = html.replace('<body>', '<body>\n' + nav, 1)
        if new_html != html:
            html    = new_html
            changed = True

    # 3. Add Related Guides panel (before </body>) if not already present
    if 'Related Playbooks' not in html and '<!-- RELATED GUIDES PANEL -->' not in html:
        panel = make_related_panel(fname, is_paper, tier)
        if panel:
            new_html = html.replace('</body>', panel + '</body>', 1)
            if new_html != html:
                html    = new_html
                changed = True

    os.makedirs(os.path.dirname(dst_path) or '.', exist_ok=True)
    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return 'patched' if changed else 'copied'


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Golf Playbooks — tier patch and distribution builder'
    )
    parser.add_argument(
        '--tier',
        choices=['standard', 'pro', 'elite'],
        default='standard',
        help="Output tier: 'standard' (default), 'pro', or 'elite'"
    )
    parser.add_argument(
        '--out',
        default=None,
        help='Output directory (default: patch in-place in source dir)'
    )
    parser.add_argument(
        '--src',
        default=None,
        help='Source directory (default: current working directory)'
    )
    args = parser.parse_args()

    src_dir = os.path.abspath(args.src or os.getcwd())
    out_dir = os.path.abspath(args.out or src_dir)
    tier    = args.tier

    os.makedirs(out_dir, exist_ok=True)

    # ── Collect HTML files to process ────────────────────────────────────
    all_html = sorted(f for f in os.listdir(src_dir)
                      if f.endswith('.html') and f not in SKIP)

    # Standard: exclude Pro-only and Elite-only files
    if tier == 'standard':
        html_files = [f for f in all_html
                      if f not in PRO_ONLY_FILES and f not in ELITE_ONLY_FILES]

    # Pro: exclude Elite-only files
    elif tier == 'pro':
        html_files = [f for f in all_html if f not in ELITE_ONLY_FILES]

    # Elite: include everything except the SKIP set
    else:
        html_files = all_html

    # ── Copy correct index into output ───────────────────────────────────
    def copy_index(src_name: str, msg: str) -> None:
        src_index = os.path.join(src_dir, src_name)
        dst_index = os.path.join(out_dir, 'index.html')
        if os.path.exists(src_index):
            shutil.copy2(src_index, dst_index)
            print(f'  {msg}')

    if tier == 'pro' and out_dir != src_dir:
        copy_index('index_pro.html', 'index_pro.html → index.html (pro)')
    elif tier == 'elite' and out_dir != src_dir:
        copy_index('index_elite.html', 'index_elite.html → index.html (elite)')
    elif tier == 'standard' and out_dir != src_dir:
        copy_index('index.html', 'index.html → index.html (standard)')

    # ── Copy non-HTML assets ──────────────────────────────────────────────
    if out_dir != src_dir:
        for asset in ASSET_FILES:
            src_asset = os.path.join(src_dir, asset)
            if os.path.exists(src_asset):
                shutil.copy2(src_asset, os.path.join(out_dir, asset))
        for asset_dir in ASSET_DIRS:
            src_adir = os.path.join(src_dir, asset_dir)
            dst_adir = os.path.join(out_dir, asset_dir)
            if os.path.exists(src_adir):
                if os.path.exists(dst_adir):
                    shutil.rmtree(dst_adir)
                shutil.copytree(src_adir, dst_adir)

    # ── Process files ─────────────────────────────────────────────────────
    print(f'\nGolf Playbooks — Tier Distribution Builder')
    print(f'  Tier:    {tier.upper()}')
    print(f'  Source:  {src_dir}')
    print(f'  Output:  {out_dir}')
    print(f'  Files:   {len(html_files)}\n')

    patched = []
    copied  = []
    unknown = []

    for fname in html_files:
        src_path = os.path.join(src_dir, fname)
        dst_path = os.path.join(out_dir, fname)

        if fname not in GUIDES and fname not in PAPER_THEME:
            unknown.append(fname)
            # Guard: skip copy if src and dst resolve to the same file (in-place run)
            if os.path.abspath(src_path) != os.path.abspath(dst_path):
                shutil.copy2(src_path, dst_path)
            continue

        result = patch_file(src_path, dst_path, tier)
        if result == 'patched':
            patched.append(fname)
        else:
            copied.append(fname)

    # ── Report ────────────────────────────────────────────────────────────
    print(f'✅ Patched ({len(patched)}):')
    for f in patched:
        print(f'   {f}')

    if copied:
        print(f'\n⏭  Already up-to-date ({len(copied)}):')
        for f in copied:
            print(f'   {f}')

    if unknown:
        print(f'\n❓ Unrecognised — copied as-is ({len(unknown)}):')
        for f in unknown:
            print(f'   {f}')

    print(f'\nDone.')
    if out_dir != src_dir:
        print(f'→ {tier.upper()} build in: {out_dir}')
        print(f'  Zip {out_dir}/ and upload to Gumroad as the {tier.capitalize()} product.')
    else:
        print('→ Files patched in-place.')
