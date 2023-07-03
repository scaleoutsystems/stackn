describe("Test of the public apps page", () => {

    beforeEach(() => {

        cy.visit("/portal/index")
    })

    it("should contain header with text Apps", () => {

        cy.get('h3').should('contain', 'Apps')
    })

})
