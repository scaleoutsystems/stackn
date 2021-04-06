def studio_url_missing():
    print("Studio URL not specified.")
    print("You have two options:")
    print("1. Pass it as an option")
    print("2. Set the environment variable STACKN_STUDIO_URL")

def project_missing():
    print("Failed to determine active project.")
    print("You have three options:")
    print("1. Pass it as an option")
    print("2. Set the environment variable STACKN_PROJECT_NAME")
    print("3. Use the command stackn set project -p <project_name>")