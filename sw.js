// Service Worker — The Scratch Project
// Version: 3.0 · 2026-06-09
// Cache: Standard (37) + Pro (3) + Elite (9) + Tools + Index pages = 64 items

const CACHE_NAME = 'scratch-project-v3-0';

const STATIC_FILES = [
  '/',
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
  '/38_practice_structure.html',
  '/39_ground_reaction_force.html',
  '/40_decision_architecture.html',
  '/41_plus_hcp_sg_targets.html',
  '/42_national_amateur_circuit.html',
  '/43_caddie_preparation.html',
  '/44_golfmetrics_deepdive.html',
  '/45_sportsbox_ai.html',
  '/46_county_team_golf.html',
  '/47_elite_performance_psychology.html',
  '/48_elite_physical_performance.html',
  '/49_advanced_game_construction.html',
  '/caddie_card.html',
  '/golf_analysis.html',
  '/golf_weekly_dashboard.html',
  '/hackmotion_playbook.html',
  '/mevo_gen2_playbook.html',
  '/practice_plan.html',
  '/swing_mechanics.html',
  '/tracking_app.html',
  '/tracking_app_v2.html',
  '/motivation.html',
  '/on_course_reference_A5_8pp.html',
  '/index.html',
  '/index_pro.html',
  '/index_elite.html',
  '/elite_tier_brief.html'
];

// Install: cache all static files
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      console.log('[SW] Installing v3.0 — caching', STATIC_FILES.length, 'files');
      return Promise.all(
        STATIC_FILES.map(function(url) {
          return cache.add(url).catch(function(err) {
            console.warn('[SW] Failed to cache:', url, err);
          });
        })
      );
    }).then(function() {
      console.log('[SW] Install complete — v3.0');
      return self.skipWaiting();
    })
  );
});

// Activate: delete old caches
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(key) {
          return key !== CACHE_NAME;
        }).map(function(key) {
          console.log('[SW] Deleting old cache:', key);
          return caches.delete(key);
        })
      );
    }).then(function() {
      console.log('[SW] Activated — v3.0 is current cache');
      return self.clients.claim();
    })
  );
});

// Fetch: cache-first with network fallback
self.addEventListener('fetch', function(event) {
  // Only handle GET requests for same-origin resources
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then(function(cached) {
      if (cached) {
        return cached;
      }
      return fetch(event.request).then(function(response) {
        // Cache successful responses
        if (response && response.status === 200 && response.type === 'basic') {
          var clone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(event.request, clone);
          });
        }
        return response;
      }).catch(function() {
        // Offline fallback — return index for navigation requests
        if (event.request.mode === 'navigate') {
          return caches.match('/index.html');
        }
      });
    })
  );
});
