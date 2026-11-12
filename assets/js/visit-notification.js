/* Page visits are independent of the browser's location permission. */
(function () {
  'use strict';
  var script = document.currentScript;
  var endpoint = script && script.getAttribute('data-visit-endpoint');
  if (!endpoint || !/^https:\/\//i.test(endpoint)) return;
  var page = window.location.pathname;
  var sessionKey = 'portfolio-visit:' + page;
  var now = Date.now();
  try {
    var last = Number(sessionStorage.getItem(sessionKey) || 0);
    if (last && now - last < 5 * 60 * 1000) return;
    sessionStorage.setItem(sessionKey, String(now));
  } catch (_) {}

  var referrer = '';
  try { referrer = new URL(document.referrer).hostname; } catch (_) {}
  var payload = {
    type: 'page_visit',
    page: page,
    title: document.title.slice(0, 160),
    referrer: referrer,
    device: /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent) ? 'mobile/tablet' : 'desktop'
  };
  fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
    credentials: 'omit',
    referrerPolicy: 'no-referrer',
    keepalive: true,
    body: JSON.stringify(payload)
  }).then(function (response) {
    if (!response.ok) throw new Error('Notification failed');
    return response.json();
  }).then(function (result) {
    if (result.ok !== true) throw new Error('Notification not acknowledged');
  }).catch(function () {
    // Allow a later page load to retry without interrupting the visitor.
    try { sessionStorage.removeItem(sessionKey); } catch (_) {}
  });
}());
