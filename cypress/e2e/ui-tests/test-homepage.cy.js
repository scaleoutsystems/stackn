describe("Test of the home page", () => {

    beforeEach(() => {

        cy.visit("/")
    })

    it("should open the home page on link click", () => {
        cy.get("li.nav-item a").contains("Home").click()
        cy.url().should("include", "")
    })

    it("should open the Apps page on link click", () => {
        cy.get("li.nav-item a").contains("Apps").click()
        cy.url().should("include", "/portal/index")
    })

    it("should open the Models page on link click", () => {
        cy.get("li.nav-item a").contains("Models").click()
        cy.url().should("include", "/models/")
    })

    it.skip("should open the User guide page on link click", () => {
        // TODO: complete when implemented
    })

    it("should open the About page on link click", () => {
        cy.get("li.nav-item a").contains("About").click()
        cy.url().should("include", "/portal/home")
    })

    it("should open the About page on link click", () => {
        cy.get("li.nav-item a").contains("About").click()
        cy.url().should("include", "/portal/home")
    })

    it("should open the signup page on link click", () => {
        cy.get("li.nav-item a").contains("Register").click()
        cy.url().should("include", "signup")
    })

    it("should open the login page on link click", () => {
        cy.get("li.nav-item a").contains("Log in").click()
        cy.url().should("include", "accounts/login")
  })
})
