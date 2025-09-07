// @ts-check

import {themes as prismThemes} from 'prism-react-renderer';
import * as dotenv from 'dotenv';

dotenv.config({path: '../.env'});

const siteUrl = process.env.DOCS_SITE_URL ?? 'https://alangunning.github.io';
const baseUrl = process.env.DOCS_BASE_URL ?? '/doc-ai/docs/';
const organizationName = process.env.GITHUB_ORG ?? 'alangunning';
const projectName = process.env.GITHUB_REPO ?? 'doc-ai';

const config = {
  title: 'Doc AI Starter',
  tagline: 'Starter template for AI document analysis',
  url: siteUrl,
  // When deploying to GitHub Pages, the base URL must match the repo name.
  baseUrl: baseUrl,
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'throw',
  favicon: 'img/favicon.ico',
  organizationName,
  projectName,
  markdown: { mermaid: true },
  themes: ['@docusaurus/theme-mermaid'],
  presets: [
    [
      'classic',
      ({
        docs: {
          path: 'content',
          sidebarPath: './sidebars.js',
          routeBasePath: '/',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],
  themeConfig: {
    navbar: {
      title: 'Doc AI Starter',
    },
    footer: {
      style: 'dark',
      copyright: `Copyright © ${new Date().getFullYear()} Alan Gunning`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  },
};

export default config;
