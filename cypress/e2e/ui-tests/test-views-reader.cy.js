describe("Test views as authenticated user", () => {

  // Tests performed as an authenticated user that only reads views
  // user: e2e_tests_login_tester

  const relurl = "/accounts/login/"

  let userdata

  before(() => {
    // username in fixture must match username in db-reset.sh
    cy.fixture('user-login.json').then(function (data) {
      userdata = data;
    })

    cy.visit(relurl);
    cy.get("[name=csrfmiddlewaretoken]")
      .should("exist")
      .should("have.attr", "value")
      .as("csrfToken");

    cy.get("@csrfToken").then((token) => {
      cy.request({
        method: "POST",
        url: relurl,
        form: true,
        body: {
          username: userdata.username,
          password: userdata.password,
        },
        headers: {
          "X-CSRFTOKEN": token,
        },
      });
    });

    cy.getCookie("sessionid").should("exist")
    cy.getCookie("csrftoken").should("exist")
  });

  beforeEach(() => {
    Cypress.Cookies.preserveOnce("sessionid", "csrftoken")
  });


  it("can view the Apps view", () => {

    cy.visit("/portal/index")
    
    cy.get('h3').should('contain', 'Apps')
  });

  it("can view the Models view", () => {
    
    cy.visit("/models/")
    
    cy.get('h3').should('contain', 'Models')
  });

  it("can view the Projects view", () => {
    
    cy.visit("/projects/")
    
    cy.get('h3').should('have.text', 'Projects')
  });

});
