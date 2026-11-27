function createButton(label, state) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'ids-button';
  button.textContent = label;
  if (state) button.dataset.state = state;
  return button;
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
    for (const [id, brand] of [['brand-a', 'Brand A'], ['brand-b', 'Brand B']]) {
      const panel = document.createElement('section');
      panel.dataset.brand = id;
      const heading = document.createElement('h2');
      heading.textContent = brand;
      panel.append(heading);
      const states = document.createElement('div');
      states.className = 'brand-comparison-states';
      for (const [caption, state] of [['Default'], ['Hover', 'hover'], ['Focused', 'focused'], ['Pressed', 'pressed']]) {
        const sample = document.createElement('div');
        const text = document.createElement('p');
        text.textContent = caption;
        sample.append(text, createButton(label, state));
        states.append(sample);
      }
      panel.append(states);
      comparison.append(panel);
    }
    return comparison;
  },
};
