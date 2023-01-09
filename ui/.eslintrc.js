module.exports = {
  root: true,
  env: {
    node: true
  },
  extends: ["plugin:vue/essential", "eslint:recommended", "@vue/prettier"],
  parserOptions: {
    parser: '@babel/eslint-parser'
  },
  rules: {
    "no-console": process.env.NODE_ENV === "production" ? "warn" : "off",
    "no-debugger": process.env.NODE_ENV === "production" ? "warn" : "off",
    "no-unused-vars": [
      "warn",
      {
        varsIgnorePattern: "'response' is assigned a value but never used"
      }
    ],
    "vue/multi-word-component-names": "off",
    "vue/no-mutating-props": "off",
    "vue/no-unused-vars": "off"
  },
  overrides: [
    {
      files: [
        "**/__tests__/*.{j,t}s?(x)",
        "**/tests/unit/**/*.spec.{j,t}s?(x)"
      ],
      env: {
        jest: true,
        jasmine: true
      },
      globals: {
        page: true,
        browser: true,
        context: true
      }
    }
  ]
};
