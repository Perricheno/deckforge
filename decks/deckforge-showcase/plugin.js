// Per-deck plugin: runs after the motion engine. Register any behavior and use it with a data attribute.
const DM = window.DeckMotion;
DM.register('heartbeat', {
  selector: '[data-heartbeat]',
  setup(el) { return t => { el.style.opacity = (0.55 + 0.45 * Math.abs(Math.sin(t * 2.2))).toFixed(3); }; },
});
