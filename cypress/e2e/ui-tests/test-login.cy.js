describe("Test login", () => {

    // username here must match username in db-cleanup.sh
    const username = "e2e_tests_login_tester"
    const pwd = "test12345"

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

    it("should login an existing user when input is valid", () => {
        cy.visit("accounts/login/")

        cy.get('input[name=username]').type(username)
        cy.get('input[name=password]').type(pwd)

        cy.get("button").contains('Login').click();

        cy.url().should("include", "projects");
        cy.get('h3').should('contain', 'Projects')
    })
})
