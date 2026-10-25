'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

for (const file of ['call.html', 'es/agendar.html', 'pt/agendar.html', 'zh/yuyue.html']) {
  test(`${file}: Cal linkReady uncovers the calendar, including after a timeout`, () => {
    const html = fs.readFileSync(path.join(__dirname, '..', file), 'utf8');
    const script = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)]
      .map(match => match[1]).find(text => text.includes('var readyTracked='));
    assert.ok(script, 'calendar initialization script exists');
    for (const late of [false, true]) {
      const callbacks = {}, events = [], timers = [];
      const elements = {
        'leon-booker': { setAttribute(name, value) { this[name] = value; } },
        'leon-cal-status': { hidden: false },
        'leon-cal-status-text': { textContent: 'Loading' },
        bookingok: { hidden: true },
        'leon-cal-direct': { href: 'https://cal.com/leonbuilds/15min?redirect=false' }
      };
      const api = (action, options) => { if (action === 'on') callbacks[options.action] = options.callback; };
      const Cal = () => {};
      Cal.ns = { leon15: api };
      const context = {
        Cal, URL, URLSearchParams,
        location: { search: '' },
        localStorage: { getItem: () => null },
        document: {
          currentScript: { closest: () => null },
          getElementById: id => elements[id],
          querySelector: () => ({ addEventListener() {} })
        },
        setTimeout(callback) { timers.push(callback); return timers.length; },
        clearTimeout() {},
        leonEvt: name => events.push(name)
      };
      context.window = context;
      vm.runInNewContext(script, context);
      if (late) {
        timers[0]();
        assert.ok(events.includes('calendar_failed'));
      }
      assert.equal(elements['leon-cal-status'].hidden, false);
      assert.equal(typeof callbacks.linkReady, 'function', 'current SDK ready event is registered');
      callbacks.linkReady();
      assert.equal(elements['leon-cal-status'].hidden, true);
      assert.equal(elements['leon-booker']['aria-busy'], 'false');
      callbacks.bookerReady();
      callbacks.linkReady();
      assert.equal(events.filter(name => name === 'calendar_ready').length, 1);
      assert.equal(elements.bookingok.hidden, true, 'readiness must not claim a booking');
    }
  });
}
