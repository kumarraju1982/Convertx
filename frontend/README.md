# PDF to Word Converter - Frontend

React + TypeScript frontend for the PDF to Word conversion service.

## Features

- Drag-and-drop file upload
- Real-time conversion progress tracking
- Responsive design (mobile and desktop)
- Accessible UI (WCAG 2.1 Level AA)
- Professional visual design with Tailwind CSS

## Requirements

- Node.js 16+
- npm or yarn

## Installation

```bash
cd frontend
npm install
```

## Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

The development server is configured to proxy API requests to `http://localhost:5000`

## Building for Production

Build the app:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## Testing

Run tests:
```bash
npm test
```

Run tests in watch mode:
```bash
npm run test:watch
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── UploadZone.tsx      # File upload component
│   │   └── ProgressDisplay.tsx # Progress tracking component
│   ├── services/
│   │   └── api.ts              # API client
│   ├── types/
│   │   └── api.ts              # TypeScript interfaces
│   ├── utils/
│   │   └── download.ts         # Download utilities
│   ├── App.tsx                 # Main app component
│   ├── main.tsx                # Entry point
│   └── index.css               # Global styles
├── public/                     # Static assets
└── package.json                # Dependencies
```

## Configuration

### API Base URL

The API base URL is configured in `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
    },
  },
}
```

For production, update the API client in `src/services/api.ts` to use your production API URL.

## Styling

The app uses Tailwind CSS for styling. Custom theme configuration is in `tailwind.config.js`.

Color scheme:
- Primary: Blue (sky)
- Success: Green
- Error: Red

## Accessibility

The app follows WCAG 2.1 Level AA guidelines:
- Keyboard navigation support
- ARIA labels and roles
- Sufficient color contrast
- Screen reader compatible

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

**API connection error:**
- Ensure backend is running on port 5000
- Check proxy configuration in `vite.config.ts`

**Build fails:**
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version (16+ required)
