/* Native browser permission only; send a rounded estimate after approval. */
(function () {
  'use strict';
  var script = document.currentScript;
  var endpoint = script && script.getAttribute('data-location-endpoint');
  if (!endpoint || !/^https:\/\//i.test(endpoint) ||
      !window.isSecureContext || !navigator.geolocation) return;

  // Respect denials and successful delivery; allow at most one later retry
  // after transient positioning/network errors, without repeatedly prompting.
  var sessionKey = 'portfolio-location-state-v2';
  var state = { attempts: 0 };
  function saveState() {
    try { sessionStorage.setItem(sessionKey, JSON.stringify(state)); } catch (_) {}
  }
  try {
    state = JSON.parse(sessionStorage.getItem(sessionKey) || 'null') || state;
  } catch (_) {}
  if (state.done || state.denied || state.attempts >= 2 || Date.now() < (state.retryAfter || 0)) return;
  state.attempts = (state.attempts || 0) + 1;
  state.retryAfter = Date.now() + 60000;
  saveState();

  navigator.geolocation.getCurrentPosition(async function (position) {
    var coords = position.coords;
    if (!Number.isFinite(coords.latitude) || !Number.isFinite(coords.longitude) ||
        !Number.isFinite(coords.accuracy)) return;
    var area = {
      latitude: Math.round(coords.latitude * 100) / 100,
      longitude: Math.round(coords.longitude * 100) / 100,
      accuracy_metres: Math.max(1500, Math.ceil(coords.accuracy / 100) * 100)
    };
    try {
      var response = await fetch(endpoint, {
        method: 'POST', headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
        credentials: 'omit', referrerPolicy: 'no-referrer',
        body: JSON.stringify({ type: 'voluntary_area', consent: true, area: area })
      });
      if (response.ok && (await response.json()).ok === true) {
        state.done = true;
        saveState();
      }
    } catch (_) {
      // Notification failures never interrupt browsing or trigger more prompts.
    }
  }, function (error) {
    // Never retry a denial or dismissal within this tab session.
    if (error && error.code === 1) {
      state.denied = true;
      saveState();
    }
  }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 0 });
}());
