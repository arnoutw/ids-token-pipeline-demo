import brandA from '../dist/site/assets/themes/brand-a/tokens.json';
import brandB from '../dist/site/assets/themes/brand-b/tokens.json';

const brands = [
  { id: 'brand-a', name: 'Brand A', tokens: brandA },
  { id: 'brand-b', name: 'Brand B', tokens: brandB },
];

const captions = { default: 'Default', hover: 'Hover', focused: 'Focused', pressed: 'Pressed' };
const platforms = [
  { id: 'web', name: 'Web', label: 'Continue' },
  { id: 'kiosk', name: 'Kiosk', label: 'Print boarding pass' },
  { id: 'onboard', name: 'Onboard', label: 'Play' },
];

function createButton(label, state) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'ids-button';
  button.textContent = label;
  if (state && state !== 'default') button.dataset.state = state;
  return button;
}

function createStateSample(label, state) {
  const sample = document.createElement('div');
  const caption = document.createElement('p');
  caption.className = 'state-caption';
  caption.textContent = captions[state];
  sample.append(caption, createButton(label, state));
  return sample;
}

export default {
  title: 'IDS / Brand Primary Button',
  args: { label: 'Continue' },
  argTypes: {
    label: { control: 'text' },
  },
  render: ({ label, state }) => createButton(label, state),
};

export const Interactive = {};
export const Hover = { args: { state: 'hover' } };
export const Focused = { args: { state: 'focused' } };
export const Pressed = { args: { state: 'pressed' } };

export const CompareBrands = {
  parameters: {
    docs: {
      source: {
        transform: (_source, { args }) => {
          const button = createButton(args.label).outerHTML;
          return brands.map(({ id }) => `<div data-brand="${id}">\n  ${button}\n</div>`).join('\n\n');
        },
      },
    },
  },
  render: ({ label }) => {
    const comparison = document.createElement('div');
    comparison.className = 'brand-comparison';
    for (const { id, name, tokens } of brands) {
      const panel = document.createElement('section');
      panel.dataset.brand = id;
      const heading = document.createElement('h2');
      heading.textContent = name;
      const typeface = document.createElement('p');
      typeface.className = 'brand-typeface';
      typeface.textContent = tokens['typography.control.font-family'].$value;
      panel.append(heading, typeface);
      const states = document.createElement('div');
      states.className = 'brand-comparison-states';
      for (const state of Object.keys(captions)) states.append(createStateSample(label, state));
      panel.append(states);
      comparison.append(panel);
    }
    return comparison;
  },
};

export const ComparePlatforms = {
  parameters: {
    docs: {
      source: {
        transform: () => platforms.map(({ id, label }) => (
          `<div data-platform="${id}">\n  ${createButton(label).outerHTML}\n</div>`
        )).join('\n\n'),
      },
    },
  },
  render: () => {
    const comparison = document.createElement('div');
    comparison.className = 'platform-comparison';
    for (const platform of platforms) {
      const group = document.createElement('section');
      group.dataset.platform = platform.id;
      const heading = document.createElement('h2');
      heading.textContent = platform.name;
      group.append(heading);
      for (const brand of brands) {
        const panel = document.createElement('div');
        panel.dataset.brand = brand.id;
        const title = document.createElement('h3');
        title.textContent = `${brand.name} · ${brand.tokens['typography.control.font-family'].$value}`;
        const samples = document.createElement('div');
        samples.className = 'platform-samples';
        for (const state of ['default', 'focused', 'pressed']) {
          samples.append(createStateSample(platform.label, state));
        }
        panel.append(title, samples);
        group.append(panel);
      }
      comparison.append(group);
    }
    return comparison;
  },
};

function createPlatformDemo(platform, instruction, actions) {
  const panel = document.createElement('section');
  panel.className = 'platform-demo';
  panel.dataset.platform = platform;
  const hint = document.createElement('p');
  hint.textContent = instruction;
  const controls = document.createElement('div');
  controls.className = 'platform-actions';
  const status = document.createElement('p');
  status.setAttribute('role', 'status');
  status.textContent = 'Ready';
  const buttons = actions.map(([label, message]) => {
    const button = createButton(label);
    button.addEventListener('click', () => { status.textContent = message; });
    controls.append(button);
    return button;
  });
  panel.append(hint, controls, status);
  return { panel, controls, buttons };
}

export const KioskTouch = {
  render: () => createPlatformDemo(
    'kiosk',
    'Tap to simulate printing a boarding pass. Switch brands in the toolbar.',
    [['Print boarding pass', 'Boarding pass sent to the demo printer.']],
  ).panel,
};

export const OnboardNavigation = {
  render: () => {
    const { panel, controls, buttons } = createPlatformDemo(
      'onboard',
      'Tap an action, or Tab to the controls and use the arrow keys and Enter.',
      [['Play', 'Playback started in the demo.'], ['Details', 'Details selected in the demo.']],
    );
    controls.addEventListener('keydown', event => {
      const direction = { ArrowLeft: -1, ArrowUp: -1, ArrowRight: 1, ArrowDown: 1 }[event.key];
      if (!direction) return;
      event.preventDefault();
      const nextIndex = Math.max(0, Math.min(buttons.length - 1, buttons.indexOf(event.target) + direction));
      buttons[nextIndex].focus();
    });
    return panel;
  },
};
