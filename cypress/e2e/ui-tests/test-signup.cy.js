describe("Test sign up", () => {

    // username here must match username in db-reset.sh
    var username = "e2e_tests_signup_" + Date.now(); // max 30 chars allowed in UI form
    const email = "no-reply-signup@scilifelab.se";
    const pwd = "test12345";

    beforeEach(() => {
        // reset and seed the database prior to every test
        if (Cypress.env('do_reset_db') === true) {
            cy.log("Resetting db state. Running db-reset.sh");
            cy.exec("./cypress/e2e/db-reset.sh");
        }
        else {
            cy.log("Skipping resetting the db state.");
        }
    })

    it("should create new user account with valid form input", () => {
        cy.visit("/signup/");

        cy.get('input[name=username]').type(username);
        cy.get('input[name=email]').type(email);
        cy.get('input[name=password1]').type(pwd);
        cy.get('input[name=password2]').type(pwd);

        cy.get("input#submit-id-save").click();

        cy.url().should("include", "accounts/login");
        cy.get('.alert-info').should('contain', 'Account created successfully!');
    })
})
