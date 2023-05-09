const { defineConfig } = require("cypress");

module.exports = defineConfig({
  env: {
    do_reset_db: true,
  },

  e2e: {
    baseUrl: 'http://studio.127.0.0.1.nip.io:8080',
    //baseUrl: 'https://serve-dev.scilifelab.se',
    experimentalSessionAndOrigin: true,

    setupNodeEvents(on, config) {
      // implement node event listeners here
      const logOptions = {
        printLogsToConsole: 'always',
      };

      require('cypress-terminal-report/src/installLogsPrinter')(on, logOptions);
    },
  },
});
