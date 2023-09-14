describe("Test views as authenticated user", () => {

  // Tests performed as an authenticated user that only reads views
  // user: e2e_tests_login_tester

  let users

  before(() => {
    // username in fixture must match username in db-reset.sh
    cy.fixture('users.json').then(function (data) {
      users = data
    })
    cy.exec("./cypress/e2e/db-reset.sh");
    cy.wait(60000);
    cy.exec("./cypress/e2e/db-seed-login.sh");
  })

  beforeEach(() => {

    cy.loginViaApi(users.login.username, users.login.password)

  })


  it("can view the Apps view", () => {

    cy.visit("/portal/index")

    cy.get('h3').should('contain', 'Apps')
  })

  it("can view the Models view", () => {

    cy.visit("/models/")

    cy.get('h3').should('contain', 'Models')
  })

  it("can view the Projects view", () => {

    cy.visit("/projects/")

    cy.get('h3').should('have.text', 'My projects')
  })

})
