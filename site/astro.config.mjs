import { defineConfig } from 'astro/config';

// Served from https://danielmevit.github.io/laydown — the base matters, or every
// asset 404s once it's deployed under the project path.
export default defineConfig({
  site: 'https://danielmevit.github.io',
  base: '/laydown',
});
