import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";
import type { Plugin } from "@docusaurus/types";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
import webpack from "webpack";

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

// Check if private fonts are available (check for actual font file, not just directory)
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fontFile = path.join(
  __dirname,
  "static/fonts/private/good_timing_bd.otf",
);
const hasPrivateFonts = fs.existsSync(fontFile);

// Read version from pyproject.toml
const pyprojectPath = path.join(__dirname, "../pyproject.toml");
if (!fs.existsSync(pyprojectPath)) {
  throw new Error(
    "pyproject.toml not found. Cannot determine project version.",
  );
}

const pyprojectContent = fs.readFileSync(pyprojectPath, "utf-8");
const versionMatch = pyprojectContent.match(/version\s*=\s*"([^"]+)"/);
if (!versionMatch) {
  throw new Error(
    "Version not found in pyproject.toml. Please ensure it contains a version field.",
  );
}

const version = versionMatch[1];

// Plugin to ignore fonts.css when private fonts aren't available.
// This allows CI to build without access to the private font submodule.
function ignoreFontsPlugin(): Plugin {
  return {
    name: "ignore-fonts-plugin",
    configureWebpack() {
      if (hasPrivateFonts) {
        return {};
      }
      return {
        plugins: [
          new webpack.IgnorePlugin({
            resourceRegExp: /fonts\.css$/,
          }),
        ],
      };
    },
  };
}

const config: Config = {
  title: "មករា",
  tagline: "Mecha-grade automation. Human-driven results.",
  favicon: "img/favicon.ico",

  customFields: {
    version,
  },

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  markdown: {
    mermaid: true,
  },
  themes: ["@docusaurus/theme-mermaid"],

  // Set the production url of your site here
  url: "https://meksys-dev.github.io",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/mekara/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "meksys-dev", // Usually your GitHub org/user name.
  projectName: "mekara", // Usually your repo name.

  onBrokenLinks: "throw",
  onBrokenAnchors: "throw",

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  plugins: [
    ignoreFontsPlugin,
    [
      "@docusaurus/plugin-content-docs",
      {
        id: "wiki",
        path: "wiki",
        routeBasePath: "wiki",
        sidebarPath: "./sidebarsWiki.ts",
        editUrl: "https://github.com/meksys-dev/mekara/tree/main/docs",
        sidebarCollapsed: false,
      },
    ],
  ],

  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.ts",
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl: "https://github.com/meksys-dev/mekara/tree/main/docs",
          sidebarCollapsed: false,
        },
        blog: false,
        theme: {
          customCss: hasPrivateFonts
            ? ["./src/css/custom.css", "./src/css/fonts.css"]
            : "./src/css/custom.css",
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: "img/mekara-full-size.jpg",
    colorMode: {
      defaultMode: "dark",
      disableSwitch: true,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: "Mekara",
      logo: {
        alt: "Meksys Mekara logo",
        src: "img/mekara-logo.png",
      },
      items: [
        {
          type: "docSidebar",
          sidebarId: "sidebar",
          position: "left",
          label: "Docs",
        },
        {
          type: "docSidebar",
          sidebarId: "wikiSidebar",
          docsPluginId: "wiki",
          position: "left",
          label: "Wiki",
        },
        {
          href: "https://github.com/meksys-dev/mekara",
          label: "Repository",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Docs",
          items: [
            {
              label: "Getting started",
              to: "/docs/",
            },
            {
              label: "Build & test",
              to: "/docs/development/build-and-test",
            },
          ],
        },
        {
          title: "More",
          items: [
            {
              label: "Meksys mekara repo",
              href: "https://github.com/meksys-dev/mekara",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Meksys.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
