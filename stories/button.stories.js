export default {
  title: 'IDS / Brand Primary Button',
  args: { label: 'Continue' },
  argTypes: {
    label: { control: 'text' },
  },
  render: ({ label, state }) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'ids-button';
    button.textContent = label;
    if (state) button.dataset.state = state;
    return button;
  },
};

export const Interactive = {};
export const Hover = { args: { state: 'hover' } };
export const Focused = { args: { state: 'focused' } };
export const Pressed = { args: { state: 'pressed' } };
