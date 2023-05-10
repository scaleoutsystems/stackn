describe("Test of the home page", () => {

    beforeEach(() => {

        cy.visit("/")
    })

    it("should display default text", () => {
        cy.get('h1.display-2').should('have.text', 'Template landing page');
    })

    it("should open a signup page on link click", () => {
        cy.get("span").contains("Sign up").click();
        cy.url().should("include", "signup");
    })

    it("should open a login page on link click", () => {
      cy.get("span").contains("Login").click();
      cy.url().should("include", "accounts/login");
  })
})
