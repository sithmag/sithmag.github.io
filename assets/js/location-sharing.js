/* Native browser permission only; send a rounded estimate after approval. */
(function () {
  'use strict';
  var script = document.currentScript;
  var endpoint = script && script.getAttribute('data-location-endpoint');
  if (!endpoint || !/^https:\/\//i.test(endpoint) ||
      !window.isSecureContext || !navigator.geolocation) return;

  // Avoid asking again as visitors navigate between pages in the same tab.
  var sessionKey = 'portfolio-location-requested';
  try {
    if (sessionStorage.getItem(sessionKey)) return;
    sessionStorage.setItem(sessionKey, '1');
  } catch (_) {
    // Browser permission still governs access when storage is unavailable.
  }

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
      await fetch(endpoint, {
        method: 'POST', headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
        credentials: 'omit', referrerPolicy: 'no-referrer',
        body: JSON.stringify({ type: 'voluntary_area', consent: true, area: area })
      });
    } catch (_) {
      // Notification failures never interrupt browsing or trigger more prompts.
    }
  }, function () {
    // Denial, dismissal, and unavailable location send nothing.
  }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 0 });
}());
