Feature: Basic Use

    Scenario: User is able to see about homepage
        Given the user accesses the url "/"
        Then the page contains the heading "Inthe.AM"

    @wip
    Scenario: User is able to generate new account
        Given the user accesses the url "/"
        And the test account user does not exist
        When the user clicks the link "Log In with Google"
        And the user enters his credentials if necessary
        Then a new account will be created using the test e-mail address
        And the page contains the heading "Terms and Conditions of Use of Inthe.AM"