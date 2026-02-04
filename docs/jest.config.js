/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    // Handle CSS modules
    "\\.module\\.css$": "identity-obj-proxy",
    "\\.css$": "identity-obj-proxy",
    // Handle docusaurus aliases
    "^@site/(.*)$": "<rootDir>/$1",
    "^@docusaurus/(.*)$": "<rootDir>/src/__mocks__/@docusaurus/$1",
  },
  testMatch: ["**/__tests__/**/*.test.{ts,tsx}"],
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        tsconfig: {
          jsx: "react-jsx",
          esModuleInterop: true,
          module: "commonjs",
          moduleResolution: "node",
        },
      },
    ],
  },
  transformIgnorePatterns: ["/node_modules/(?!(@docusaurus|@mdx-js)/)"],
};
