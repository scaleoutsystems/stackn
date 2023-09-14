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

    it("should open the User guide page on link click", () => {
        cy.get("li.nav-item a").contains("User guide").click()
        cy.url().should("include", "/docs/")
        cy.get('[data-cy="sidebar-title"]').should('contain', 'user guide') // check that the sidebar title is there, comes from our templates
        cy.get('.col-lg-8 > h1').should('contain', 'Congratulations') // check that the page content is there, comes from django-wiki templates
    })

    it("should open the signup page on link click", () => {
        cy.get("li.nav-item a").contains("Register").click()
        cy.url().should("include", "signup")
    })

    it("should open the login page on link click", () => {
        cy.get("li.nav-item a").contains("Log in").click()
        cy.url().should("include", "accounts/login")
  })

    it("should have proper title", () => {
	cy.get("title").should("have.text", "Home | SciLifeLab Serve")
    })
})
