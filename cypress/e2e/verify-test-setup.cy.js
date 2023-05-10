describe("Simple tests to verify the test framework setup", () => {

  it("passes", () => {
  })

  it("cypress can log to the terminal", () => {
    cy.log("Verify that this message is output to the terminal.")
  })

  it("can access and parse the test fixtures", () => {
    cy.fixture('users.json').then(function (data) {
      cy.log(data.login.username)
      cy.log(data.contributor.username)
      cy.log(data.contributor.email)
    })
  })

})
