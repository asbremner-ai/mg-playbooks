#!/usr/bin/env python3
"""
Golf Playbooks — Navigation & Tier Patch Script
=================================================
Run inside your local GitHub repository folder:

    # Generate both distributions:
    python3 patch_playbooks.py --tier standard --out dist/standard
    python3 patch_playbooks.py --tier pro      --out dist/pro

    # Patch in-place (existing behaviour, defaults to standard):
    python3 patch_playbooks.py

What it does for every playbook HTML file:
  1. Adds a "⌂ All Playbooks" Home nav bar at the very top.
  2. Adds a "Related Playbooks" panel at the very bottom.
  3. In --tier pro mode: sets TIER = 'pro' in the inline script constant,
     which causes all data-tier="pro" elements to render.
  4. In --tier standard mode (default): sets TIER = 'standard',
     which causes all data-tier="pro" elements to be removed on load.
  5. Skips index.html (standard) and index_pro.html (pro has its own).
  6. Safe to re-run — already-patched files are detected by tier marker.

The TIER constant approach:
  Each playbook that contains advanced content has this near the top of
  its <script> block (inserted by this script if not present):

      const TIER = 'standard'; // patched by patch_playbooks.py

  And a tiny init block:
      document.querySelectorAll('[data-tier="pro"]').forEach(el => {
        if (TIER !== 'pro') el.remove();
      });

  Advanced tabs carry:  <button class="tab" data-tier="pro" ...>
  Advanced sections:    <div class="sec" data-tier="pro" id="...">
  Advanced sub-sections within existing tabs carry:
                        <div class="pro-section" data-tier="pro">
"""

# <!-- version:v3.0 · 2026-06-07 · patch_playbooks.py -->

import os, re, shutil, argparse

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
    # Pro-only stubs
    '38_practice_structure.html':  ('Practice Structure Science', '🔬', '#c8922a'),
    '39_ground_reaction_force.html':('Ground Reaction Force',     '⚡', '#c8922a'),
    '40_decision_architecture.html':('Decision Architecture & EV','🎯', '#c8922a'),
}

# ── Pro-only files (not included in standard distribution)
PRO_ONLY_FILES = {
    '38_practice_structure.html',
    '39_ground_reaction_force.html',
    '40_decision_architecture.html',
    'index_pro.html',
}

# ── Files to skip entirely (no patching)
SKIP = {'index.html', 'index_pro.html', 'sw.js', 'manifest.json', 'patch_playbooks.py'}

# ── Paper-theme files (light background)
PAPER_THEME = {'on_course_reference_A5_8pp.html'}

# ── Related guides map (unchanged from v2.2)
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
    '37_approach_zone.html':       ['03_longgame_pro.html','22_wedge_distances.html','11_shot_dispersion.html','mevo_gen2_playbook.html','26_stats_interpretation.html'],
    # Pro-only stubs link back to related core guides
    '38_practice_structure.html':  ['05_pre_shot_routine.html','26_stats_interpretation.html','18_training_aids_2.html','17_progress_journal.html'],
    '39_ground_reaction_force.html':['03_longgame_pro.html','06_golf_fitness.html','25_speed_training.html','mevo_gen2_playbook.html'],
    '40_decision_architecture.html':['20_course_management.html','11_shot_dispersion.html','26_stats_interpretation.html','24_competitive_strategy.html'],
}


# ── TIER INJECTION ──────────────────────────────────────────────────────────

TIER_SCRIPT_MARKER = '/* tier-init */'

def make_tier_script(tier: str) -> str:
    """Returns the inline script block that controls tier rendering."""
    return f"""<script>
/* tier-init */
const TIER = '{tier}'; // 'standard' | 'pro' — set by patch_playbooks.py
(function() {{
  document.addEventListener('DOMContentLoaded', function() {{
    document.querySelectorAll('[data-tier="pro"]').forEach(function(el) {{
      if (TIER !== 'pro') {{
        el.remove();
      }} else {{
        // Pro elements: ensure they display and carry the pro visual marker
        el.setAttribute('data-pro-active', '1');
      }}
    }});
  }});
}})();
</script>"""


def inject_tier(html: str, tier: str) -> str:
    """Injects or replaces the TIER constant script block."""
    new_script = make_tier_script(tier)
    # Replace existing tier block if present
    if TIER_SCRIPT_MARKER in html:
        # Remove entire existing tier script block
        html = re.sub(
            r'<script>\s*/\* tier-init \*/.*?</script>',
            '',
            html,
            flags=re.DOTALL
        )
    # Inject before closing </head>
    if '</head>' in html:
        html = html.replace('</head>', new_script + '\n</head>', 1)
    return html


# ── NAV BUILDERS ────────────────────────────────────────────────────────────

def make_home_nav(is_paper: bool, tier: str = 'standard') -> str:
    if tier == 'pro':
        index_file = 'index_pro.html'
        badge = (
            '<span style="font-family:\'JetBrains Mono\',monospace;font-size:8px;'
            'letter-spacing:0.18em;text-transform:uppercase;color:#e8b050;'
            'background:rgba(200,146,42,0.12);border:1px solid rgba(200,146,42,0.35);'
            'padding:3px 8px;border-radius:3px;">⬡ Pro Edition</span>'
        )
    else:
        index_file = 'index.html'
        badge = (
            '<span style="font-family:\'Courier New\',monospace;font-size:9px;'
            'letter-spacing:0.18em;text-transform:uppercase;'
            'color:rgba(232,240,216,0.2);">The Scratch Project</span>'
        )

    if is_paper:
        return (
            f'<!-- HOME NAV -->\n'
            f'<div style="background:#f5f0e8;border-bottom:1px solid rgba(120,100,60,0.2);'
            f'padding:10px 20px;display:flex;align-items:center;justify-content:space-between;">\n'
            f'  <a href="{index_file}" style="font-family:\'Courier Prime\',\'Courier New\',monospace;'
            f'font-size:10px;letter-spacing:0.22em;text-transform:uppercase;color:rgba(60,50,30,0.55);'
            f'text-decoration:none;display:inline-flex;align-items:center;gap:8px;">'
            f'<span style="font-size:14px;line-height:1;">&#8962;</span> All Playbooks</a>\n'
            f'  {badge}\n'
            f'</div>\n'
        )
    else:
        return (
            f'<!-- HOME NAV -->\n'
            f'<div style="background:#111e11;border-bottom:1px solid rgba(160,200,80,0.2);'
            f'padding:10px 20px;display:flex;align-items:center;justify-content:space-between;'
            f'position:relative;z-index:200;">\n'
            f'  <a href="{index_file}" style="font-family:\'Courier New\',monospace;font-size:10px;'
            f'letter-spacing:0.22em;text-transform:uppercase;color:rgba(232,240,216,0.55);'
            f'text-decoration:none;display:inline-flex;align-items:center;gap:8px;">'
            f'<span style="font-size:14px;line-height:1;">&#8962;</span> All Playbooks</a>\n'
            f'  {badge}\n'
            f'</div>\n'
        )


def make_related_panel(fname: str, is_paper: bool) -> str:
    rels = RELATED.get(fname, [])
    if not rels:
        return ''

    if is_paper:
        outer_bg   = '#f5f0e8'
        outer_bdr  = 'rgba(120,100,60,0.2)'
        label_col  = 'rgba(120,100,60,0.6)'
        card_bg    = 'rgba(0,0,0,0.04)'
        card_bdr   = 'rgba(0,0,0,0.1)'
        card_text  = '#2a2010'
        footer_col = 'rgba(60,50,30,0.4)'
        font_body  = "'Courier Prime','Courier New',monospace"
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


# ── FILE PROCESSOR ──────────────────────────────────────────────────────────

def patch_file(src_path: str, dst_path: str, tier: str) -> str:
    fname = os.path.basename(src_path)
    is_paper = fname in PAPER_THEME

    with open(src_path, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()

    changed = False

    # 1. Inject/update TIER constant
    html_new = inject_tier(html, tier)
    if html_new != html:
        html = html_new
        changed = True

    # 2. Add Home nav
    if 'All Playbooks' not in html and '<!-- HOME NAV -->' not in html:
        nav = make_home_nav(is_paper, tier)
        new_html = html.replace('<body>\n', '<body>\n' + nav, 1)
        if new_html == html:
            new_html = html.replace('<body>', '<body>\n' + nav, 1)
        if new_html != html:
            html = new_html
            changed = True
    elif '<!-- HOME NAV -->' in html and tier == 'pro':
        # Update home nav link to point to index_pro.html
        html_new = html.replace('href="index.html"', 'href="index_pro.html"', 1)
        if html_new != html:
            html = html_new
            changed = True

    # 3. Add Related Guides panel
    if 'Related Playbooks' not in html and '<!-- RELATED GUIDES PANEL -->' not in html:
        panel = make_related_panel(fname, is_paper)
        if panel:
            new_html = html.replace('</body>', panel + '</body>', 1)
            if new_html != html:
                html = new_html
                changed = True

    os.makedirs(os.path.dirname(dst_path) or '.', exist_ok=True)
    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return 'patched' if changed else 'copied'


# ── MAIN ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Golf Playbooks tier patch and distribution builder'
    )
    parser.add_argument(
        '--tier',
        choices=['standard', 'pro'],
        default='standard',
        help="Output tier: 'standard' (default) or 'pro'"
    )
    parser.add_argument(
        '--out',
        default=None,
        help="Output directory (default: patch in-place in cwd)"
    )
    parser.add_argument(
        '--src',
        default=None,
        help="Source directory (default: current working directory)"
    )
    args = parser.parse_args()

    src_dir = args.src or os.getcwd()
    out_dir = args.out or src_dir
    tier    = args.tier

    os.makedirs(out_dir, exist_ok=True)

    html_files = [f for f in os.listdir(src_dir) if f.endswith('.html') and f not in SKIP]
    html_files.sort()

    # Filter pro-only files for standard tier
    if tier == 'standard':
        html_files = [f for f in html_files if f not in PRO_ONLY_FILES]
    
    # For pro tier, copy index_pro.html as index.html in output
    if tier == 'pro':
        pro_index_src = os.path.join(src_dir, 'index_pro.html')
        if os.path.exists(pro_index_src):
            shutil.copy2(pro_index_src, os.path.join(out_dir, 'index.html'))
            print(f"Copied index_pro.html → {out_dir}/index.html")

    print(f"\nGolf Playbooks Navigation & Tier Patch")
    print(f"Tier:      {tier.upper()}")
    print(f"Source:    {src_dir}")
    print(f"Output:    {out_dir}")
    print(f"Files:     {len(html_files)}\n")

    patched = []
    copied  = []
    unknown = []

    for fname in html_files:
        src_path = os.path.join(src_dir, fname)
        dst_path = os.path.join(out_dir, fname)

        if fname not in GUIDES and fname not in PAPER_THEME:
            unknown.append(fname)
            # Still copy even if not in registry
            shutil.copy2(src_path, dst_path)
            continue

        result = patch_file(src_path, dst_path, tier)
        if result == 'patched':
            patched.append(fname)
        else:
            copied.append(fname)

    # Copy non-HTML assets (sw.js, manifest, icons etc.)
    for f in os.listdir(src_dir):
        if not f.endswith('.html') and f not in ('patch_playbooks.py',):
            src = os.path.join(src_dir, f)
            dst = os.path.join(out_dir, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)

    print(f"✅ Patched ({len(patched)}):")
    for f in patched:
        print(f"   {f}")

    if copied:
        print(f"\n📋 Copied unchanged ({len(copied)}):")
        for f in copied:
            print(f"   {f}")

    if unknown:
        print(f"\n❓ Unrecognised — copied raw ({len(unknown)}):")
        for f in unknown:
            print(f"   {f}")

    print(f"\nDone.")
    print(f"→ {tier.upper()} build in: {out_dir}")
    if tier == 'standard':
        print(f"  Zip {out_dir}/ and upload to Gumroad as Product A.")
    else:
        print(f"  Zip {out_dir}/ and upload to Gumroad as Product B (Pro Edition).")
