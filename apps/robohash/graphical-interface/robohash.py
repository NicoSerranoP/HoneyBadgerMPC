# This Python file uses the following encoding: utf-8
import os
import hashlib
from PIL import Image
import natsort


class Robohash():
    """
    Robohash is a quick way of generating unique avatars for a site.
    The original use-case was to create somewhat memorable images to represent a RSA key.
    """

    def __init__(self, string, rfunc, hashcount=11, ignoreext=True):
        """
        Creates our Robohasher
        Takes in the string to make a Robohash out of.
        """

        # Optionally remove an images extension before hashing.
        if ignoreext is True:
            string = self._remove_exts(string)

        mom, dad = string.split(":")
        mom = mom.encode("utf-8")
        dad = dad.encode("utf-8")

        #momhex = hashlib.sha512(mom).hexdigest()
        #dadhex = hashlib.sha512(dad).hexdigest()

        momhex = mom
        dadhex = dad
        # momhex = mom
        # dadhex = dad

        # print(momhex)
        # print(dadhex)

        self.hasharray = self._mix_hashes(hashcount, momhex, dadhex, rfunc)
        self.mom_hasharray = self._create_hashes(hashcount, momhex)
        self.dad_hasharray = self._create_hashes(hashcount, dadhex)

        # Start this at 4, so earlier is reserved
        # 0 = Color
        # 1 = Set
        # 2 = bgset
        # 3 = BG
        self.iter = 4

        self.resourcedir = os.path.dirname(__file__) + "/"
        # Get the list of backgrounds and RobotSets
        self.sets = self._listdirs(self.resourcedir + "sets")
        self.bgsets = self._listdirs(self.resourcedir + "backgrounds")

        # Get the colors in set1
        self.colors = self._listdirs(self.resourcedir + "sets/set1")
        self.format = "png"

    def _remove_exts(self, string):
        """
        Sets the string, to create the Robohash
        """

        # If the user hasn't disabled it, we will detect image extensions, such as .png, .jpg, etc.
        # We'll remove them from the string before hashing.
        # This ensures that /Bear.png and /Bear.bmp will send back the same image, in different formats.

        if string.lower().endswith(
                (".png", ".gif", ".jpg", ".bmp", ".jpeg", ".ppm", ".datauri")
        ):
            fmt = string[string.rfind(".") + 1 : len(string)]
            if fmt.lower() == "jpg":
                fmt = "jpeg"
            self.format = fmt
            string = string[0 : string.rfind(".")]
        return string

    def _mix_hashes(self, count, mom, dad, rfunc):
        """
        Breaks up our hash into slots, so we can pull them out later.
        Essentially, it splits our SHA/MD5/etc into X parts.
        """
        hasharray = []
        blocksize = int(len(mom) / count)
        mom_color = int(mom[0:blocksize], 16)
        dad_color = int(dad[0:blocksize], 16)
        for i in range(0, count):
            # Get 1/numblocks of the hash
            currentstart = (1 + i) * blocksize - blocksize
            currentend = (1 + i) * blocksize
            if rfunc():
                hasharray.append((int(mom[currentstart:currentend], 16), mom_color))
            else:
                hasharray.append((int(dad[currentstart:currentend], 16), dad_color))
        return hasharray

    def _create_hashes(self, count, robo):
        """
        Breaks up our hash into slots, so we can pull them out later.
        Essentially, it splits our SHA/MD5/etc into X parts.
        """
        hasharray = []
        blocksize = int(len(robo) / count)
        robo_color = int(robo[0:blocksize], 16)
        for i in range(0, count):
            # Get 1/numblocks of the hash
            currentstart = (1 + i) * blocksize - blocksize
            currentend = (1 + i) * blocksize
            hasharray.append((int(robo[currentstart:currentend], 16), robo_color))
        return hasharray

    def _listdirs(self, path):
        return [
            d
            for d in natsort.natsorted(os.listdir(path))
            if os.path.isdir(os.path.join(path, d))
        ]

    def _get_list_of_files(self, path, hasharray):
        """
        Go through each subdirectory of `path`, and choose one file from each to use in our hash.
        Continue to increase self.iter, so we use a different 'slot' of randomness each time.
        """
        chosen_files = []

        for i in range(4, len(hasharray)):
            color = self.colors[hasharray[i][1] % len(self.colors)]
            colored_path = os.path.join(path, color)
            files_in_dir = []

            part_path = None
            if i == 4:
                part_path = os.path.join(colored_path, "004#02Face")
            elif i == 5:
                part_path = os.path.join(colored_path, "000#Mouth")
                print(part_path)
            elif i == 6:
                part_path = os.path.join(colored_path, "003#01Body")
                print(part_path)
            elif i == 7:
                part_path = os.path.join(colored_path, "002#Accessory")
                print(part_path)
            elif i == 8:
                part_path = os.path.join(colored_path, "001#Eyes")
                print(part_path)
            else:
                break

            for imagefile in natsort.natsorted(os.listdir(part_path)):
                files_in_dir.append(os.path.join(part_path, imagefile))
            element_in_list = hasharray[i][0] % len(files_in_dir)
            chosen_files.append(files_in_dir[element_in_list])
        return chosen_files

    def assemble(self, roboset=None, format=None, bgset=None, sizex=300, sizey=300):
        """
        Build our Robot!
        Returns the robot image itself.
        """

        # Allow users to manually specify a robot 'set' that they like.
        # Ensure that this is one of the allowed choices, or allow all
        # If they don't set one, take the first entry from sets above.

        if roboset == "any":
            roboset = self.sets[self.hasharray[1] % len(self.sets)]
        elif roboset in self.sets:
            roboset = roboset
        else:
            roboset = self.sets[0]

        # Only set1 is setup to be color-seletable. The others don't have enough pieces in various colors.
        # This could/should probably be expanded at some point..
        # Right now, this feature is almost never used. ( It was < 44 requests this year, out of 78M reqs )
        # Child hasharray[a, b, c], parts_from[m, d, m]

        # If they specified a background, ensure it's legal, then give it to them.
        if bgset in self.bgsets:
            bgset = bgset
        elif bgset == "any":
            bgset = self.bgsets[self.hasharray[2] % len(self.bgsets)]

        # If we set a format based on extension earlier, use that. Otherwise, PNG.
        if format is None:
            format = self.format

        # Each directory in our set represents one piece of the Robot, such as the eyes, nose, mouth, etc.

        # Each directory is named with two numbers - The number before the # is the sort order.
        # This ensures that they always go in the same order when choosing pieces, regardless of OS.

        # The second number is the order in which to apply the pieces.
        # For instance, the head has to go down BEFORE the eyes, or the eyes would be hidden.

        # First, we'll get a list of parts of our robot.

        mom_roboparts = self._get_list_of_files(
            self.resourcedir + "sets/set1/", self.mom_hasharray
        )
        mom_roboparts.sort(key=lambda x: x.split("#")[1])

        dad_roboparts = self._get_list_of_files(
            self.resourcedir + "sets/set1/", self.dad_hasharray
        )
        dad_roboparts.sort(key=lambda x: x.split("#")[1])

        roboparts = self._get_list_of_files(
            self.resourcedir + "sets/set1/", self.hasharray
        )
        roboparts.sort(key=lambda x: x.split("#")[1])

        if bgset is not None:
            bglist = []
            backgrounds = natsort.natsorted(
                os.listdir(self.resourcedir + "backgrounds/" + bgset)
            )
            backgrounds.sort()
            for ls in backgrounds:
                if not ls.startswith("."):
                    bglist.append(self.resourcedir + "backgrounds/" + bgset + "/" + ls)
            background = bglist[self.hasharray[3] % len(bglist)]

        mom_roboimg = Image.open(mom_roboparts[0])
        mom_roboimg = mom_roboimg.resize((1024, 1024))
        for png in mom_roboparts:
            img = Image.open(png)
            img = img.resize((1024, 1024))
            mom_roboimg.paste(img, (0, 0), img)

        dad_roboimg = Image.open(dad_roboparts[0])
        dad_roboimg = dad_roboimg.resize((1024, 1024))
        for png in dad_roboparts:
            img = Image.open(png)
            img = img.resize((1024, 1024))
            dad_roboimg.paste(img, (0, 0), img)

        # Paste in each piece of the Robot.
        roboimg = Image.open(roboparts[0])
        roboimg = roboimg.resize((1024, 1024))
        for png in roboparts:
            img = Image.open(png)
            img = img.resize((1024, 1024))
            roboimg.paste(img, (0, 0), img)

        # If we're a BMP, flatten the image.
        if format == "bmp":
            # Flatten bmps
            r, g, b, a = roboimg.split()
            roboimg = Image.merge("RGB", (r, g, b))

        if bgset is not None:
            bg = Image.open(background)
            bg = bg.resize((1024, 1024))
            bg.paste(roboimg, (0, 0), roboimg)
            roboimg = bg

        self.child_img = roboimg.resize((sizex, sizey), Image.ANTIALIAS)
        self.mom_img = mom_roboimg.resize((sizex, sizey), Image.ANTIALIAS)
        self.dad_img = dad_roboimg.resize((sizex, sizey), Image.ANTIALIAS)
        self.format = format