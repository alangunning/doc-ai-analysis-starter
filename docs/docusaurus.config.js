// @ts-check

import {themes as prismThemes} from 'prism-react-renderer';

const config = {
  title: 'Doc Analysis AI Starter',
  tagline: 'Starter template for AI document analysis',
  url: 'https://YOUR_GITHUB_USERNAME.github.io',
  baseUrl: '/',
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'YOUR_GITHUB_USERNAME',
  projectName: 'doc-analysis-ai-starter',
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
      title: 'Doc Analysis AI Starter',
    },
    footer: {
      style: 'dark',
      copyright: `Copyright © ${new Date().getFullYear()} Doc Analysis AI Starter`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  },
};

export default config;
