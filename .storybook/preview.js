import '../dist/site/assets/tokens.css';
import '../site/button.css';
import './preview.css';

export default {
  globalTypes: {
    brand: {
      name: 'Brand',
      description: 'Brand tokens inherited by the preview',
      toolbar: {
        icon: 'paintbrush',
        items: [
          { value: 'brand-a', title: 'Brand A' },
          { value: 'brand-b', title: 'Brand B' },
        ],
        dynamicTitle: true,
      },
    },
  },
  initialGlobals: { brand: 'brand-a' },
  decorators: [
    (story, { globals }) => {
      const preview = document.createElement('div');
      preview.dataset.brand = globals.brand;
      preview.style.padding = '8px';
      preview.append(story());
      return preview;
    },
  ],
  parameters: {
    layout: 'centered',
  },
};
