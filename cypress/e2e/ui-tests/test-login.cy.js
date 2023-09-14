describe("Test login", () => {

    let users

    before(() => {
        // reset and seed the database ONCE prior to all tests in this class
        if (Cypress.env('do_reset_db') === true) {
            // pre-creates a test user for this test
            cy.log("Resetting db state. Running db-reset.sh");
            cy.exec("./cypress/e2e/db-reset.sh");
            cy.wait(60000);
            cy.exec("./cypress/e2e/db-seed-contributor.sh");
        }
        else {
            cy.log("Skipping resetting the db state.");
        }
    })

    beforeEach(() => {
        // username in fixture must match username in db-reset.sh
        cy.fixture('users.json').then(function (data) {
            users = data;
          })
    })

    it("can login an existing user through the UI when input is valid", () => {

        cy.visit("accounts/login/")
	



        cy.get('input[name=username]').type(users.contributor.username)
        cy.get('input[name=password]').type(users.contributor.password)

        cy.get("button").contains('Login').click()
            .then((href) => {
                cy.log(href)
                cy.url().should("include", "projects")
                cy.get('h3').should('contain', 'My projects')
            })
    })

    it("can login an existing user through the UI when input is valid using cypress command", () => {

        cy.loginViaUI(users.contributor.username, users.contributor.password)

    })

    it("Should have proper title", () => {
	cy.visit("accounts/login/")
        cy.get("title").should("have.text", "Login | SciLifeLab Serve")
    })
})
