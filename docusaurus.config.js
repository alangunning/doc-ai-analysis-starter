// @ts-check

import {themes as prismThemes} from 'prism-react-renderer';

const config = {
  title: 'Doc AI Analysis Starter',
  tagline: 'Starter template for AI document analysis',
  url: 'https://YOUR_GITHUB_USERNAME.github.io',
  baseUrl: '/',
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'YOUR_GITHUB_USERNAME',
  projectName: 'doc-ai-analysis-starter',
  presets: [
    [
      'classic',
      ({
        docs: {
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
      title: 'Doc AI Analysis Starter',
    },
    footer: {
      style: 'dark',
      copyright: `Copyright © ${new Date().getFullYear()} Doc AI Analysis Starter`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  },
};

export default config;
