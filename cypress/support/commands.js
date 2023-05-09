// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

Cypress.Commands.add('loginViaUI', (username, password) => {
    cy.session(
      username,
      () => {
        cy.visit('/accounts/login/')
        cy.get('input[name=username]').type(username)
        cy.get('input[name=password]').type(`${password}{enter}`, { log: false })
        cy.url().should('include', '/projects')
        cy.get('h3').should('contain', 'Projects')
      },
      {
        validate: () => {
          cy.getCookie('sessionid').should('exist')
          cy.getCookie('csrftoken').should('exist')
        },
      }
    )
  })

Cypress.Commands.add('loginViaApi', (username, password) => {

    const relurl = "/accounts/login/"

    cy.session(
      username,
      () => {
        cy.visit(relurl)

        cy.get("[name=csrfmiddlewaretoken]")
        .should("exist")
        .should("have.attr", "value")
        .as("csrfToken");

        cy.get("@csrfToken").then((token) => {
            cy.request({
              method: "POST",
              url: relurl,
              form: true,
              body: {
                username: username,
                password: password,
              },
              headers: {
                "X-CSRFTOKEN": token,
              },
            });
          });
      },
      {
        validate: () => {
          cy.getCookie('sessionid').should('exist')
          cy.getCookie('csrftoken').should('exist')
        },
      }
    )
  })
