import itchat
import my_glob


def profile_pic(remarkname=None, username=None):
    if remarkname is None and username is None: return ""
    if username is None:
        username = my_glob._to_UN(remarkname)
    else:
        remarkname = my_glob._to_NN(username)
    if username == "None":
        return ""
    filename = "|".join(map(str,map(ord, remarkname))) + ".jpg"
    fileImage = open(filename, "wb")
    fileImage.write(itchat.get_head_img(userName=username))
    fileImage.close()
    return filename


def get_signature(remarkname=None, username=None):
    if remarkname is None and username is None: return ""
    if username is None:
        username = my_glob._to_UN(remarkname)
    if username == "None":
        return ""
    return itchat.search_friends(userName=username).get("Signature", "")
