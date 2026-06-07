#!/usr/bin/env python3
"""
Golf Playbooks — Navigation Patch Script
=========================================
Run this script once inside your local GitHub repository folder.

    cd /path/to/your/mg-playbooks-repo
    python3 patch_playbooks.py

What it does for every playbook HTML file:
  1. Adds a "⌂ All Playbooks" Home nav bar at the very top.
  2. Adds a "Related Playbooks" panel at the very bottom.
  3. Skips index.html and any file already patched.

Safe to re-run — already-patched files are detected and skipped.
"""

# <!-- version:v2.2 · 2026-06-07 · patch_playbooks.py -->

import os, re

# ── Guide registry: filename → (display title, emoji, accent colour)
GUIDES = {
    '01_putting_pro.html':         ('Putting Playbook',           '🎯', '#e8b800'),
    '02_shortgame_pro.html':       ('Short Game Playbook',        '🌊', '#2ec4b6'),
    '03_longgame_pro.html':        ('Long Game Playbook',         '🏌️', '#5ecb3e'),
    '04_complete_golfer.html':     ('The Complete Golfer',        '🧭', '#ff6b35'),
    '05_pre_shot_routine.html':    ('Pre-Shot Routine',           '🔁', '#5ecb3e'),
    '06_golf_fitness.html':        ('Golf Fitness Plan',          '💪', '#ff6b35'),
    '07_golf_nutrition.html':      ('Golf Nutrition Plan',        '🍎', '#5ecb3e'),
    '08_pro_round_prep.html':      ('Pro Round Prep',             '🗺️', '#e8b800'),
    '09_golf_coach_ai.html':       ('Golf Coach AI',              '🤖', '#5ecb3e'),
    '10_scratch_plan.html':        ('24-Month Scratch Plan',      '🏆', '#e8b800'),
    '11_shot_dispersion.html':     ('Shot Dispersion Mapping',    '📊', '#5ecb3e'),
    '12_rules_of_golf.html':       ('Rules of Golf',              '📜', '#e8b800'),
    '13_injury_prevention.html':   ('Injury Prevention',          '🩺', '#ff6b35'),
    '14_video_analysis.html':      ('Video Analysis',             '🎥', '#2ec4b6'),
    '15_equipment_fitting.html':   ('Equipment Fitting',          '🔧', '#e8b800'),
    '16_solo_pressure_round.html': ('Solo Pressure Round',        '🔥', '#ff6b35'),
    '17_progress_journal.html':    ('Progress Journal',           '📓', '#9b72f5'),
    '18_training_aids_2.html':     ('Training Arsenal',           '🛠️', '#5ecb3e'),
    '20_course_management.html':   ('Course Management',          '⚖️', '#e8b800'),
    '21_mental_game.html':         ('Mental Game Mastery',        '🧘', '#9b72f5'),
    '22_wedge_distances.html':     ('Wedge Distance Matrix',      '📏', '#e8b800'),
    '23_weather_conditions.html':  ('Weather & Conditions',       '🌬️', '#2ec4b6'),
    '24_competitive_strategy.html':('Competitive Strategy',       '🏆', '#e8b800'),
    '25_speed_training.html':      ('Speed Training',             '⚡', '#5ecb3e'),
    '26_stats_interpretation.html':('Stats & SG Interpretation',  '🔢', '#2ec4b6'),
    '27_six_month_plan.html':      ('Months 1–6 Plan',            '📅', '#e8b800'),
    '28_months_7_12_plan.html':    ('Months 7–12 Plan',           '📆', '#e8b800'),
    '29_months_13_18_plan.html':   ('Months 13–18 Plan',          '🎯', '#c8921a'),
    '30_months_19_24_plan.html':   ('Months 19–24 Plan',          '🏆', '#3a8a3a'),
    'caddie_card.html':            ('Caddie Reference Card',       '📋', '#2ec4b6'),
    'swing_mechanics.html':        ('Swing Mechanics',            '⚙️', '#5ecb3e'),
    'golf_analysis.html':          ('Launch Monitor Analysis',    '📈', '#2ec4b6'),
    'practice_plan.html':          ('4-Week Programme',           '🗓️', '#2ec4b6'),
    'mevo_gen2_playbook.html':     ('Mevo Gen2 Data Mastery',     '📡', '#2ec4b6'),
    'hackmotion_playbook.html':    ('HackMotion Data Mastery',    '🖥️', '#2ec4b6'),
    'golf_weekly_dashboard.html':  ('Weekly Practice Dashboard',  '📅', '#5ecb3e'),
    'motivation.html':             ('The Honest Case for Scratch', '🔥', '#a0c850'),
    'on_course_reference_A5_8pp.html': ('On-Course Reference A5', '📄', '#48b0a8'),
    'tracking_app.html':           ('Performance Tracker v1',     '📊', '#2ec4b6'),
    'tracking_app_v2.html':        ('Performance Tracker',        '📊', '#5ecb3e'),
    '31_on_course_notes.html':     ('On-Course Notes',            '🗺️', '#5ecb3e'),
    '32_putting_green_reading.html':('Green Reading Deep Dive',   '📐', '#5ecb3e'),
    '33_competitive_pathway.html': ('UK Competitive Pathway',     '🏆', '#5ecb3e'),
    '34_coaching_relationship.html':('The Coaching Relationship', '🎓', '#2ec4b6'),
    '35_links_travel_golf.html':   ('Links & Travel Golf',        '🌊', '#5ecb3e'),
    '36_playing_partners.html':    ('Playing Partners',           '🤝', '#2ec4b6'),
    '37_approach_zone.html':       ('The 100–175 Yard Zone',      '🎯', '#e8b800'),
}

# ── Related guides map: filename → [related filenames in priority order]
RELATED = {
    '01_putting_pro.html':         ['02_shortgame_pro.html','18_training_aids_2.html','05_pre_shot_routine.html','17_progress_journal.html','09_golf_coach_ai.html'],
    '02_shortgame_pro.html':       ['01_putting_pro.html','22_wedge_distances.html','18_training_aids_2.html','05_pre_shot_routine.html','15_equipment_fitting.html'],
    '03_longgame_pro.html':        ['swing_mechanics.html','11_shot_dispersion.html','25_speed_training.html','14_video_analysis.html','mevo_gen2_playbook.html'],
    '04_complete_golfer.html':     ['10_scratch_plan.html','21_mental_game.html','05_pre_shot_routine.html','17_progress_journal.html','26_stats_interpretation.html'],
    '05_pre_shot_routine.html':    ['21_mental_game.html','16_solo_pressure_round.html','08_pro_round_prep.html','04_complete_golfer.html'],
    '06_golf_fitness.html':        ['25_speed_training.html','07_golf_nutrition.html','13_injury_prevention.html','10_scratch_plan.html'],
    '07_golf_nutrition.html':      ['06_golf_fitness.html','08_pro_round_prep.html','13_injury_prevention.html','10_scratch_plan.html'],
    '08_pro_round_prep.html':      ['05_pre_shot_routine.html','20_course_management.html','07_golf_nutrition.html','21_mental_game.html','12_rules_of_golf.html'],
    '09_golf_coach_ai.html':       ['26_stats_interpretation.html','mevo_gen2_playbook.html','hackmotion_playbook.html','17_progress_journal.html'],
    '10_scratch_plan.html':        ['27_six_month_plan.html','28_months_7_12_plan.html','29_months_13_18_plan.html','30_months_19_24_plan.html','17_progress_journal.html'],
    '11_shot_dispersion.html':     ['03_longgame_pro.html','mevo_gen2_playbook.html','20_course_management.html','09_golf_coach_ai.html'],
    '12_rules_of_golf.html':       ['08_pro_round_prep.html','24_competitive_strategy.html','16_solo_pressure_round.html'],
    '13_injury_prevention.html':   ['06_golf_fitness.html','25_speed_training.html','07_golf_nutrition.html'],
    '14_video_analysis.html':      ['swing_mechanics.html','03_longgame_pro.html','hackmotion_playbook.html','09_golf_coach_ai.html'],
    '15_equipment_fitting.html':   ['01_putting_pro.html','mevo_gen2_playbook.html','11_shot_dispersion.html','09_golf_coach_ai.html'],
    '16_solo_pressure_round.html': ['21_mental_game.html','05_pre_shot_routine.html','24_competitive_strategy.html','17_progress_journal.html'],
    '17_progress_journal.html':    ['26_stats_interpretation.html','09_golf_coach_ai.html','10_scratch_plan.html','16_solo_pressure_round.html'],
    '18_training_aids_2.html':     ['mevo_gen2_playbook.html','hackmotion_playbook.html','01_putting_pro.html','02_shortgame_pro.html','03_longgame_pro.html'],
    '20_course_management.html':   ['08_pro_round_prep.html','11_shot_dispersion.html','24_competitive_strategy.html','23_weather_conditions.html'],
    '21_mental_game.html':         ['05_pre_shot_routine.html','16_solo_pressure_round.html','08_pro_round_prep.html','24_competitive_strategy.html'],
    '22_wedge_distances.html':     ['02_shortgame_pro.html','mevo_gen2_playbook.html','11_shot_dispersion.html'],
    '23_weather_conditions.html':  ['20_course_management.html','08_pro_round_prep.html','03_longgame_pro.html'],
    '24_competitive_strategy.html':['21_mental_game.html','12_rules_of_golf.html','16_solo_pressure_round.html','08_pro_round_prep.html'],
    '25_speed_training.html':      ['06_golf_fitness.html','03_longgame_pro.html','mevo_gen2_playbook.html','13_injury_prevention.html'],
    '26_stats_interpretation.html':['09_golf_coach_ai.html','mevo_gen2_playbook.html','17_progress_journal.html','10_scratch_plan.html'],
    '27_six_month_plan.html':      ['10_scratch_plan.html','28_months_7_12_plan.html','29_months_13_18_plan.html','30_months_19_24_plan.html'],
    '28_months_7_12_plan.html':    ['10_scratch_plan.html','27_six_month_plan.html','29_months_13_18_plan.html','30_months_19_24_plan.html'],
    'swing_mechanics.html':        ['03_longgame_pro.html','14_video_analysis.html','hackmotion_playbook.html','mevo_gen2_playbook.html'],
    'golf_analysis.html':          ['09_golf_coach_ai.html','mevo_gen2_playbook.html','11_shot_dispersion.html','10_scratch_plan.html'],
    'practice_plan.html':          ['10_scratch_plan.html','27_six_month_plan.html','18_training_aids_2.html','17_progress_journal.html'],
    'mevo_gen2_playbook.html':     ['hackmotion_playbook.html','09_golf_coach_ai.html','11_shot_dispersion.html','26_stats_interpretation.html'],
    'hackmotion_playbook.html':    ['mevo_gen2_playbook.html','09_golf_coach_ai.html','swing_mechanics.html','14_video_analysis.html'],
    '29_months_13_18_plan.html':   ['10_scratch_plan.html','28_months_7_12_plan.html','30_months_19_24_plan.html','24_competitive_strategy.html','17_progress_journal.html'],
    '30_months_19_24_plan.html':   ['10_scratch_plan.html','29_months_13_18_plan.html','24_competitive_strategy.html','17_progress_journal.html','21_mental_game.html'],
    'caddie_card.html':            ['22_wedge_distances.html','23_weather_conditions.html','11_shot_dispersion.html','20_course_management.html'],
    'golf_weekly_dashboard.html':  ['tracking_app_v2.html','17_progress_journal.html','26_stats_interpretation.html','10_scratch_plan.html'],
    'motivation.html':             ['10_scratch_plan.html','04_complete_golfer.html','27_six_month_plan.html','21_mental_game.html'],
    'on_course_reference_A5_8pp.html': ['caddie_card.html','22_wedge_distances.html','23_weather_conditions.html','20_course_management.html'],
    'tracking_app.html':           ['tracking_app_v2.html','17_progress_journal.html','26_stats_interpretation.html','09_golf_coach_ai.html'],
    'tracking_app_v2.html':        ['17_progress_journal.html','26_stats_interpretation.html','09_golf_coach_ai.html','10_scratch_plan.html'],
    '31_on_course_notes.html':     ['20_course_management.html','08_pro_round_prep.html','caddie_card.html','17_progress_journal.html','26_stats_interpretation.html'],
    '32_putting_green_reading.html':['01_putting_pro.html','31_on_course_notes.html','23_weather_conditions.html','20_course_management.html','caddie_card.html'],
    '33_competitive_pathway.html': ['24_competitive_strategy.html','10_scratch_plan.html','16_solo_pressure_round.html','21_mental_game.html','26_stats_interpretation.html'],
    '34_coaching_relationship.html':['09_golf_coach_ai.html','14_video_analysis.html','mevo_gen2_playbook.html','17_progress_journal.html','hackmotion_playbook.html'],
    '35_links_travel_golf.html':   ['23_weather_conditions.html','20_course_management.html','02_shortgame_pro.html','21_mental_game.html','caddie_card.html'],
    '36_playing_partners.html':    ['21_mental_game.html','05_pre_shot_routine.html','24_competitive_strategy.html','33_competitive_pathway.html'],
    '37_approach_zone.html':       ['03_longgame_pro.html','22_wedge_distances.html','20_course_management.html','26_stats_interpretation.html','mevo_gen2_playbook.html'],
}

# Files that use the paper/ink design (not the dark green theme)
PAPER_THEME = {'10_scratch_plan.html', '27_six_month_plan.html', '28_months_7_12_plan.html', '29_months_13_18_plan.html', '30_months_19_24_plan.html'}
# Files to skip entirely
SKIP = {'index.html'}


def make_home_nav(is_paper: bool) -> str:
    if is_paper:
        bg, border, text, sub = '#3d2e1a', 'rgba(26,18,8,0.3)', 'rgba(245,239,228,0.55)', 'rgba(245,239,228,0.2)'
    else:
        bg, border, text, sub = '#111e11', 'rgba(160,200,80,0.2)', 'rgba(232,240,216,0.55)', 'rgba(232,240,216,0.2)'
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


def make_related_panel(filename: str, is_paper: bool) -> str:
    rels = RELATED.get(filename, [])
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
        if r not in GUIDES:
            continue
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


def patch_file(filepath: str) -> str:
    fname = os.path.basename(filepath)
    is_paper = fname in PAPER_THEME

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()

    changed = False

    # 1. Add Home nav after <body> if not already present
    if 'All Playbooks' not in html and '<!-- HOME NAV -->' not in html:
        nav = make_home_nav(is_paper)
        new_html = html.replace('<body>\n', '<body>\n' + nav, 1)
        if new_html == html:
            new_html = html.replace('<body>', '<body>\n' + nav, 1)
        if new_html != html:
            html = new_html
            changed = True

    # 2. Add Related Guides panel before </body> if not already present
    if 'Related Playbooks' not in html and '<!-- RELATED GUIDES PANEL -->' not in html:
        panel = make_related_panel(fname, is_paper)
        if panel:
            new_html = html.replace('</body>', panel + '</body>', 1)
            if new_html != html:
                html = new_html
                changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

    return 'patched' if changed else 'already up-to-date'


# ── Main
if __name__ == '__main__':
    cwd = os.getcwd()
    html_files = [f for f in os.listdir(cwd) if f.endswith('.html') and f not in SKIP]
    html_files.sort()

    print(f"Golf Playbooks Navigation Patch")
    print(f"Directory: {cwd}")
    print(f"Files found: {len(html_files)}\n")

    patched = []
    skipped = []
    unknown = []

    for fname in html_files:
        if fname not in GUIDES and fname not in PAPER_THEME:
            unknown.append(fname)
            continue
        result = patch_file(os.path.join(cwd, fname))
        if result == 'patched':
            patched.append(fname)
        else:
            skipped.append(fname)

    print(f"✅ Patched ({len(patched)}):")
    for f in patched:
        print(f"   {f}")

    if skipped:
        print(f"\n⏭  Already up-to-date ({len(skipped)}):")
        for f in skipped:
            print(f"   {f}")

    if unknown:
        print(f"\n❓ Unrecognised — skipped ({len(unknown)}):")
        for f in unknown:
            print(f"   {f}")

    print(f"\nDone. Commit and push to GitHub to publish.")
