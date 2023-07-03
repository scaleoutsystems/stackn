describe("Test of the public models page", () => {

    beforeEach(() => {

        cy.visit("/models/")
    })

    it("should contain header with text Models", () => {

        cy.get('h3').should('contain', 'Models')
    })

    it("should contain text about no public models", () => {

        cy.get('p').should('contain', 'No publicly published services available.')
    })

})
