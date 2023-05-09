describe("Test login", () => {

    let userdata

    before(() => {
        // reset and seed the database ONCE prior to all tests in this class
        if (Cypress.env('do_reset_db') === true) {
            // pre-creates a test user for this test
            cy.log("Resetting db state. Running db-reset.sh");
            cy.exec("./cypress/e2e/db-reset.sh");
        }
        else {
            cy.log("Skipping resetting the db state.");
        }
    })

    beforeEach(() => {
        // username in fixture must match username in db-reset.sh
        cy.fixture('user-login.json').then(function (data) {
            userdata = data;
          })
    })

    it("can login an existing user through the UI when input is valid", () => {

        cy.visit("accounts/login/")

        cy.get('input[name=username]').type(userdata.username)
        cy.get('input[name=password]').type(userdata.password)

        cy.get("button").contains('Login').click();

        cy.url().should("include", "projects");
        cy.get('h3').should('contain', 'Projects')
    })
})
