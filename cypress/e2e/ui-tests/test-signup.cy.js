describe("Test sign up", () => {

    let userdata

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

    beforeEach(() => {
        // username in fixture must match username in db-reset.sh
        cy.fixture('user-signup.json').then(function (data) {
            userdata = data;
            userdata.username = data.username_prefix + Date.now(); // max 30 chars allowed in UI form
          })
    })

    it("should create new user account with valid form input", () => {
 
        cy.visit("/signup/");
        cy.get("title").should("have.text", "Sign Up | SciLifeLab Serve")

        cy.get('input[name=username]').type(userdata.username);
        cy.get('input[name=email]').type(userdata.email);
        cy.get('input[name=password1]').type(userdata.password);
        cy.get('input[name=password2]').type(userdata.password);

        cy.get("input#submit-id-save").click();

        cy.url().should("include", "accounts/login");
        cy.get('.alert-info').should('contain', 'Account created successfully!');
    })
})
