describe("Test project contributor user functionality", () => {

    // Tests performed as an authenticated user that
    // creates and deletes objects.
    // user: e2e_tests_contributor_tester

    let users

    before(() => {
        // seed the db with: contributor user, a blank project
        cy.log("Seeding the db for the contributor tests. Running db-seed-contributor.sh");
        cy.exec("./cypress/e2e/db-reset.sh")
        cy.wait(60000)
        cy.visit("/")
        cy.log("Running seed_contributor.py")
        cy.exec("./cypress/e2e/db-seed-contributor.sh")
    })

    beforeEach(() => {
        // username in fixture must match username in db-reset.sh
        cy.log("Logging in as contributor user")
        cy.fixture('users.json').then(function (data) {
            users = data

            cy.loginViaApi(users.contributor.username, users.contributor.password)
        })
    })


    it("can run the test setup", () => {
    })

    it("can create a new blank project", () => {

        // Names of objects to create
        const project_name = "e2e-create-proj-test"
        const volume_name = "e2e-project-vol"
        const project_title_name = project_name + " | SciLifeLab Serve"

        cy.visit("/projects/")
        cy.get("title").should("have.text", "My projects | SciLifeLab Serve")

        // Click button for UI to create a new project
        cy.get("a").contains('New project').click()
        cy.url().should("include", "projects/templates")
        cy.get('h3').should('contain', 'New project')

        // Next click button to create a new blank project
        cy.get("a").contains('Create').first().click()
        cy.url().should("include", "projects/create?template=")
        cy.get('h3').should('contain', 'New project')

        // Fill in the options for creating a new blank project
        cy.get('input[name=name]').type(project_name)
        cy.get('textarea[name=description]').type("A test project created by an e2e test.")
        cy.get("input[name=save]").contains('Create project').click()
            .then((href) => {
                cy.log(href)
                //cy.url().should("include", "/project-e2e-blank");
                cy.get("title").should("have.text", project_title_name)
                cy.get('h3').should('contain', project_name)

                // Check that project settings are available
                cy.get('[data-cy="settings"]').click()
                cy.url().should("include", "settings")
                cy.get('h3').should('contain', 'Project settings')
            })

        // TODO: add additional asserts

    })

    it.skip("can create a new mlflow project", () => {
    })

    it("can delete a project", () => {

        // Names of objects to create
        const project_name = "e2e-delete-proj-test"

        cy.visit("/projects/")

        // Verify that the test project has been created
        cy.get('h5.card-title').should('contain', project_name)

        cy.get('div#modalConfirmDelete').should('have.css', 'display', 'none')

        // Next click button to delete the project
        cy.get('h5.card-title').contains(project_name).siblings('div').find('a.confirm-delete').click()
            .then((href) => {
                cy.get('div#modalConfirmDelete').should('have.css', 'display', 'block')

                cy.get("h1#modalConfirmDeleteLabel").then(function($elem) {
                    cy.log($elem.text())

                    cy.get('div#modalConfirmDeleteFooter').find('button').contains('Delete').click()

                    // Assert that the project has been deleted
                    cy.contains(project_name).should('not.exist')
               })
            })
    })
})
