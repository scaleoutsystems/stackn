class Version:
    def __init__(self, version='v0.0.0'):

        numbers = version[1:].split('.')
        self.major = int(numbers[0])
        self.minor = int(numbers[1])
        self.patch = int(numbers[2])
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise Exception(
                'Major, minor, patch should be nonegative integers.')

    # Release a new version
    # Default is new minor version
    def release(self, release_type='minor'):
        if release_type == 'minor':
            self.minor = self.minor+1
            self.patch = 0
        elif release_type == 'patch':
            self.patch = self.patch+1
        elif release_type == 'major':
            self.major = self.major+1
            self.minor = 0
            self.patch = 0
        else:
            return False, "Incorrect release type (major, minor, patch)."

        return True, self.__str__()

    # Implement comparison operators to allow for sorting
    # of models
    def __gt__(self, other):
        if self.major > other.major:
            return True
        elif other.major > self.major:
            return False

        if self.minor > other.minor:
            return True
        elif other.minor > self.minor:
            return False

        if self.patch > other.patch:
            return True
        elif other.patch > self.patch:
            return False

        return False

    def __eq__(self, other):
        if self.major == other.major and self.minor == other.minor and self.patch == other.minor:
            return True

        return False

    def __lt__(self, other):
        if other.__gt__(self) or self.__eq__(other):
            return False

        return True

    def release_types(self):
        return ['major', 'minor', 'patch']

    def __str__(self):
        return 'v{}.{}.{}'.format(self.major, self.minor, self.patch)
