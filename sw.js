// ─────────────────────────────────────────────────────────
// The Scratch Project — Service Worker
// Version: 2.3 · 2026-05-31
// Strategy: Cache-first for all static assets
//           Network-first for external APIs (Golf Coach AI)
// ─────────────────────────────────────────────────────────

const CACHE_NAME = 'scratch-project-v2-4';

// All HTML files to cache on install
const STATIC_FILES = [
  '/',
  '/index.html',
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
// Pre-cache all static files when the service worker installs.
// Uses individual try/catch so one failed file doesn't block the rest.

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async cache => {
      console.log('[SW] Installing — caching', STATIC_FILES.length, 'files');

      // Cache HTML files individually so a single failure doesn't abort
      for (const url of STATIC_FILES) {
        try {
          await cache.add(url);
        } catch (err) {
          console.warn('[SW] Failed to cache:', url, err.message);
        }
      }

      // Cache font CSS with CORS mode
      for (const url of FONT_URLS) {
        try {
          const response = await fetch(url, { mode: 'cors' });
          if (response.ok) await cache.put(url, response);
        } catch (err) {
          console.warn('[SW] Failed to cache font:', url);
        }
      }

      console.log('[SW] Install complete');
    })
  );
  // Activate immediately — don't wait for old SW to finish
  self.skipWaiting();
});

// ─── ACTIVATE ──────────────────────────────────────────────
// Delete any old cache versions when a new SW takes over.

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
// Request interception strategy:
//   • Network-only for Anthropic API and Firebase (always live)
//   • Cache-first for all guide HTML and fonts
//   • Network-with-cache-fallback for everything else

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // 1. Always go to network for API calls — never serve from cache
  const isNetworkOnly = NETWORK_ONLY.some(domain => url.hostname.includes(domain));
  if (isNetworkOnly) {
    event.respondWith(fetch(event.request));
    return;
  }

  // 2. Cache-first for local HTML files and manifest
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        if (cached) return cached;
        // Not in cache yet — fetch, cache, and return
        return fetch(event.request).then(response => {
          if (response.ok) {
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, response.clone());
            });
          }
          return response;
        }).catch(() => {
          // Completely offline and not cached — return offline page
          if (event.request.mode === 'navigate') {
            return caches.match('/index.html');
          }
        });
      })
    );
    return;
  }

  // 3. Cache-first for Google Fonts (same domain as CSS fetches)
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
          // Fonts unavailable offline — browser falls back to system fonts gracefully
          return new Response('', { status: 408 });
        });
      })
    );
    return;
  }

  // 4. Everything else — try network, fall back to cache
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
// Allows pages to trigger a cache refresh (e.g. after a repo update).
// Send { type: 'SKIP_WAITING' } from any page to force SW update.

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
