import brandA from '../dist/site/assets/themes/brand-a/tokens.json';
import brandB from '../dist/site/assets/themes/brand-b/tokens.json';

const brands = [
  { id: 'brand-a', name: 'Brand A', tokens: brandA },
  { id: 'brand-b', name: 'Brand B', tokens: brandB },
];

const captions = { default: 'Default', hover: 'Hover', focused: 'Focused', pressed: 'Pressed' };

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
