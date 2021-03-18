import psycopg2

"""
Student naam: Bram van Leusden
Studentnummer" 1779320
"""

dbname = "huwebshop"
dbpassword = "Postpoep"

recommendation_type = int(input('typ een "1" voor content filtering en een "2" voor colabretive filtering'))

profile_ids = ["'5a393d68ed295900010384ca'", "'5a394ce4a825610001bb7d7b'",
               "'5a39567fed2959000103a539'", "'5a399285a825610001bbe8e1'"]
x = 0
for i in profile_ids:
    x += 1
    print(f"{x}:{i}")
selection = int(input("select a profile by inputting its number:"))

selectedprofid = profile_ids[selection-1]




def most_frequent(lst):
    """
    reference: https://www.geeksforgeeks.org/python-find-most-frequent-element-in-a-list/

    finds the most common element of a list
    :param lst: lst
    :return: list
    """
    return max(set(lst), key=lst.count)


def connect_to_database(dbname, dbpassword):
    """
    makes an connection with a specified postgres databse

    :param dbname: name of the databse (tuple)
    :param dbpassword: password of postgres (tuple)
    :return: Tuple
    """
    c = psycopg2.connect(f"dbname={dbname} user=postgres password={dbpassword}")
    cur = c.cursor()

    return c, cur


def get_profile_products(profid):
    """
    fetches the product id's from a chosen profile id

    :param profid: chosen profile id (tuple)
    :return: list
    """
    connection, cursor = connect_to_database(dbname, dbpassword)

    cursor.execute(f"SELECT prodid FROM profiles_previously_viewed WHERE profid = {profid}")
    viewed = cursor.fetchall()
    viewed_lst = []

    for i in viewed:
        viewed_lst.append(i[0])

    cursor.close()
    connection.close()

    return viewed_lst





def get_product_categorys(profid):
    """
    gathers the most popular product category of a selected profile

    :param: a chosen profile id (tuple)
    :return: two lists
    """
    connection, cursor = connect_to_database(dbname, dbpassword)
    viewed_products = get_profile_products(profid)

    category_lst = []
    subcategory_lst = []

    for i in viewed_products:
        cursor.execute(f"SELECT id, category, subcategory FROM products WHERE id = '{i}'")
        raw_product_data = cursor.fetchall()
        for i in raw_product_data:
            category_lst.append(i[1])
            subcategory_lst.append(i[2])

    main_category = most_frequent(category_lst)
    main_subcategory = most_frequent(subcategory_lst)

    cursor.close()
    connection.close()

    return main_category, main_subcategory


def recommend_products_contentfiltering():
    """
    recommends 5 products based on what category's the a selected profile has bought

    :return: three lists
    """
    connection, cursor = connect_to_database(dbname, dbpassword)
    category, subcategory = get_product_categorys(selectedprofid)
    cursor.execute(f"SELECT id, category, subcategory "
                   f"FROM products "
                   f"WHERE category = '{category}' and subcategory = '{subcategory}'"
                   f"LIMIT 5")
    raw_data = cursor.fetchall()

    id_lst = []
    category_lst = []
    subcategory_lst = []
    for i in raw_data:
        id_lst.append(i[0])
        category_lst.append(i[1])
        subcategory_lst.append(i[2])


    cursor.close()
    connection.close()


    return id_lst, category_lst, subcategory_lst


def recommend_products_collabritvefiltering():
    """
    recomends products using the collabritive filtering method

    :return: tuple, 3 lists
    """
    connection, cursor = connect_to_database(dbname, dbpassword)
    main_category, main_subcategory = get_product_categorys(selectedprofid)

    cursor.execute(f"SELECT profid FROM profiles_previously_viewed WHERE profid NOT LIKE{selectedprofid}")
    all_profid = cursor.fetchall()

    profid_lst = []

    for i in all_profid:
        profid_lst.append(i[0])

    # refrence for this peice of code:
    # https://careerkarma.com/blog/python-remove-duplicates-from-list/#:~:text=You%20can%20remove%20duplicates%20from,whose%20duplicates%20have%20been%20removed.
    profid_lst_final = list(dict.fromkeys(profid_lst))

    for p in profid_lst_final:
        rec_category, rec_subcategory = get_product_categorys(f"'{p}'")

        if rec_category == main_category and rec_subcategory == main_subcategory:
            cursor.execute(f"SELECT prodid FROM profiles_previously_viewed WHERE profid ='{p}'")
            raw_profiledata = cursor.fetchall()

            rec_prodid_lst = []

            for i in raw_profiledata:
                rec_prodid_lst.append(i[0])

            for i in rec_prodid_lst:
                cursor.execute(f"SELECT id, category, subcategory "
                               f"FROM products "
                               f"WHERE id ='{i}'")
                raw_data = cursor.fetchall()

                prod_id_lst = []
                prod_category_lst = []
                prod_subcategory_lst = []
                for i in raw_data:
                    prod_id_lst.append(i[0])
                    prod_category_lst.append(i[1])
                    prod_subcategory_lst.append(i[2])

            return p, prod_id_lst, prod_category_lst, prod_subcategory_lst
        else:
            continue


def make_fill_table_contentfiltering():
    """
    makes a table in postgres with the given recommendations

    :return: NONE
    """
    x = 0
    connection, cursor = connect_to_database(dbname, dbpassword)

    id_lst, category_lst, subcategory_lst = recommend_products_contentfiltering()

    cursor.execute(f"DROP TABLE IF EXISTS recommendation;"
                   f"CREATE TABLE recommendation ("
                   f"product_id VARCHAR(255),"
                   f"category VARCHAR(255),"
                   f"subcategory VARCHAR(255),"
                   f"PRIMARY KEY (product_id)"
                   f"); ")

    for i in range(5):
        cursor.execute(f"INSERT INTO recommendation VALUES('{id_lst[x]}', '{category_lst[x]}', '{subcategory_lst[x]}')")
        x += 1

    connection.commit()

    cursor.close()
    connection.close()

    print("procces finished")


def make_fill_table_colabretivefiltering():
    """
    makes a table in postgres with the given recommendations

    :return: NONE
    """
    x = 0
    connection, cursor = connect_to_database(dbname, dbpassword)

    profile_id, prodid_lst, category_lst, subcategory_lst = recommend_products_collabritvefiltering()

    cursor.execute(f"DROP TABLE IF EXISTS recommendation;"
                   f"CREATE TABLE recommendation ("
                   f"prof_id VARCHAR(255),"
                   f"product_id VARCHAR(255),"
                   f"category VARCHAR(255),"
                   f"subcategory VARCHAR(255),"
                   f"PRIMARY KEY (prof_id)"
                   f"); ")

    for i in range(len(prodid_lst)):
        cursor.execute(f"INSERT INTO recommendation VALUES('{profile_id}','{prodid_lst[x]}', '{category_lst[x]}', '{subcategory_lst[x]}')")
        x += 1

    connection.commit()

    cursor.close()
    connection.close()

    print("procces finished")


if recommendation_type == 1:
    make_fill_table_contentfiltering()
else:
    make_fill_table_colabretivefiltering()

