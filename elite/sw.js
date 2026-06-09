// ─────────────────────────────────────────────────────────
// The Scratch Project — Service Worker
// Version: 2.5 · 2026-06-08
// Strategy: Cache-first for all static assets
//           Network-first for external APIs (Golf Coach AI)
// ─────────────────────────────────────────────────────────

const CACHE_NAME = 'scratch-project-v2-5';

// All HTML files to cache on install
const STATIC_FILES = [
  '/',
  '/index.html',
  '/index_pro.html',
  '/index_elite.html',
  '/01_putting_pro.html',
  '/02_shortgame_pro.html',
  '/03_longgame_pro.html',
  '/04_complete_golfer.html',
  '/05_pre_shot_routine.html',
  '/06_golf_fitness.html',
  '/07_golf_nutrition.html',
  '/08_pro_round_prep.html',
  '/09_golf_coach_ai.html',
  '/10_scratch_plan.html',
  '/11_shot_dispersion.html',
  '/12_rules_of_golf.html',
  '/13_injury_prevention.html',
  '/14_video_analysis.html',
  '/15_equipment_fitting.html',
  '/16_solo_pressure_round.html',
  '/17_progress_journal.html',
  '/18_training_aids_2.html',
  '/20_course_management.html',
  '/21_mental_game.html',
  '/22_wedge_distances.html',
  '/23_weather_conditions.html',
  '/24_competitive_strategy.html',
  '/25_speed_training.html',
  '/26_stats_interpretation.html',
  '/27_six_month_plan.html',
  '/28_months_7_12_plan.html',
  '/29_months_13_18_plan.html',
  '/30_months_19_24_plan.html',
  '/31_on_course_notes.html',
  '/32_putting_green_reading.html',
  '/33_competitive_pathway.html',
  '/34_coaching_relationship.html',
  '/35_links_travel_golf.html',
  '/36_playing_partners.html',
  '/37_approach_zone.html',
  // Pro-only guides
  '/38_practice_structure.html',
  '/39_ground_reaction_force.html',
  '/40_decision_architecture.html',
  // Elite-only guides
  '/41_plus_hcp_sg_targets.html',
  '/42_national_amateur_circuit.html',
  '/43_caddie_preparation.html',
  '/44_golfmetrics_deepdive.html',
  '/45_sportsbox_ai.html',
  '/46_county_team_golf.html',
  '/47_elite_performance_psychology.html',
  '/48_elite_physical_performance.html',
  '/49_advanced_game_construction.html',
  // Tools and apps
  '/caddie_card.html',
  '/golf_analysis.html',
  '/golf_weekly_dashboard.html',
  '/hackmotion_playbook.html',
  '/mevo_gen2_playbook.html',
  '/motivation.html',
  '/on_course_reference_A5_8pp.html',
  '/practice_plan.html',
  '/swing_mechanics.html',
  '/tracking_app.html',
  '/tracking_app_v2.html',
  '/manifest.json'
];

// External font URLs to cache (both variants used across guides)
const FONT_URLS = [
  'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap',
  'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap',
  'https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap'
];

// APIs that always need a live connection — never cache
const NETWORK_ONLY = [
  'api.anthropic.com',
  'firebaseio.com',
  'googleapis.com/identitytoolkit',
  'securetoken.googleapis.com'
];

// ─── INSTALL ───────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async cache => {
      console.log('[SW] Installing v2.5 — caching', STATIC_FILES.length, 'files');
      for (const url of STATIC_FILES) {
        try {
          await cache.add(url);
        } catch (err) {
          console.warn('[SW] Failed to cache:', url, err.message);
        }
      }
      for (const url of FONT_URLS) {
        try {
          const response = await fetch(url, { mode: 'cors' });
          if (response.ok) await cache.put(url, response);
        } catch (err) {
          console.warn('[SW] Failed to cache font:', url);
        }
      }
      console.log('[SW] Install complete — v2.5');
    })
  );
  self.skipWaiting();
});

// ─── ACTIVATE ──────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => {
            console.log('[SW] Deleting old cache:', key);
            return caches.delete(key);
          })
      );
    }).then(() => {
      console.log('[SW] Activated — version', CACHE_NAME);
      return self.clients.claim();
    })
  );
});

// ─── FETCH ─────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  const isNetworkOnly = NETWORK_ONLY.some(domain => url.hostname.includes(domain));
  if (isNetworkOnly) {
    event.respondWith(fetch(event.request));
    return;
  }

  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        if (cached) return cached;
        return fetch(event.request).then(response => {
          if (response.ok) {
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, response.clone());
            });
          }
          return response;
        }).catch(() => {
          if (event.request.mode === 'navigate') {
            return caches.match('/index.html');
          }
        });
      })
    );
    return;
  }

  if (url.hostname.includes('fonts.googleapis.com') || url.hostname.includes('fonts.gstatic.com')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        if (cached) return cached;
        return fetch(event.request, { mode: 'cors' }).then(response => {
          if (response.ok) {
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, response.clone());
            });
          }
          return response;
        }).catch(() => {
          return new Response('', { status: 408 });
        });
      })
    );
    return;
  }

  event.respondWith(
    fetch(event.request).then(response => {
      if (response.ok) {
        caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, response.clone());
        });
      }
      return response;
    }).catch(() => caches.match(event.request))
  );
});

// ─── MESSAGE HANDLER ───────────────────────────────────────
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
