// @ts-check

import {themes as prismThemes} from 'prism-react-renderer';

const config = {
  title: 'AI Doc Analysis Starter',
  tagline: 'Starter template for AI document analysis',
  url: 'https://alangunning.github.io',
  baseUrl: '/',
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'alangunning',
  projectName: 'ai-doc-analysis-starter',
  presets: [
    [
      'classic',
      ({
        docs: {
          path: 'content',
          sidebarPath: require.resolve('./sidebars.js'),
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],
  themeConfig: {
    navbar: {
      title: 'AI Doc Analysis Starter',
    },
    footer: {
      style: 'dark',
      copyright: `Copyright © ${new Date().getFullYear()} AI Doc Analysis Starter`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  },
};

export default config;
