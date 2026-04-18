from flask import Flask, render_template, request, redirect, url_for, session
from db import get_connection # function to connect with MySQL database
from datetime import date, datetime, timedelta


app = Flask(__name__)
app.secret_key = "anything123"

# home page 
@app.route("/")
def home():
    return render_template("home.html")

#########################################################/sales/new######################
@app.route("/sales/new")
def sales_new():
    # this variable will hold the selected customer data
    # at the beginning, no customer is selected
    selected_customer = None

    # get the customer id from session (if the user selected a customer before)
    cid = session.get("sale_customer_id")

    # if there is a customer id saved in session
    if cid:
        # connect to the database
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # get the customer data using the customer id
        cur.execute(
            "SELECT * FROM customer WHERE customer_id = %s",
            (cid,)
        )

        # fetch the selected customer record
        selected_customer = cur.fetchone()

        # close database connection
        cur.close()
        conn.close()

    # send the selected customer (or none) to the html page
    return render_template("sales_new.html", customer=selected_customer)





########################################################    VIEW     ###############################################################

# view customers table
@app.route("/customers")
def customers():
    conn = get_connection() # connect to database
    cur = conn.cursor(dictionary=True)  # use dictionary cursor to access columns by name
    cur.execute("SELECT * FROM customer ORDER BY customer_id ")  # get all customers 
    rows = cur.fetchall()
    # close database connection
    cur.close()
    conn.close()
    return render_template("customers_list.html", customers=rows)  # send customers list to HTML page

########################################################     ADD     ###############################################################
# this route is used to add a new customer
@app.route("/customers/new", methods=["GET", "POST"])
def create_customer():

    # if the user submits the form
    if request.method == "POST":
        # read customer data from the form
        first_name = request.form["first_name"].strip()
        last_name  = request.form["last_name"].strip()
        email      = request.form["email"].strip()
        phone      = request.form["phone"].strip()

        # connect to the database
        conn = get_connection()
        cur = conn.cursor()

        # insert new customer into customer table
        cur.execute(
            "INSERT INTO customer (first_name, last_name, email, phone) VALUES (%s, %s, %s, %s)",
            (first_name, last_name, email, phone)
        )
        conn.commit()

        # get the id of the newly added customer
        new_id = cur.lastrowid

        # close database connection
        cur.close()
        conn.close()

        # if this customer was added during create order
        if request.args.get("from") == "sale":
            # save customer id in session for the current sale
            session["sale_customer_id"] = new_id

            # go back to create order page
            return redirect(url_for("sales_new"))

        # if customer was added normally (not from sale)
        return render_template("success.html", message="Customer saved successfully!")

    else:
        # if GET request, show add customer form
        return render_template("customer_form.html")

# this route shows all customers so the user can pick one for the sale
@app.route("/customers/pick")
def customers_pick():

    # get search keyword from url (if exists)
    q = request.args.get("q", "").strip()

    # connect to the database
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # if the user searched for a customer
    if q:
        # search by name, phone, or email
        cur.execute("""
            SELECT * FROM customer
            WHERE first_name LIKE %s OR last_name LIKE %s
               OR phone LIKE %s OR email LIKE %s
            ORDER BY customer_id
        """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        # if no search, show all customers
        cur.execute("SELECT * FROM customer ORDER BY customer_id")

    # fetch all customers
    rows = cur.fetchall()

    # close database connection
    cur.close()
    conn.close()

    # send customers list to html page
    return render_template("customers_pick.html", customers=rows, q=q)


# this route is called when the user selects a customer for the sale
@app.route("/customers/use/<int:customer_id>")
def customers_use_for_sale(customer_id):

    # save the selected customer id in session
    session["sale_customer_id"] = customer_id

    # go back to create order page
    return redirect(url_for("sales_new"))

####----------------------------------

@app.route("/sales/order-info", methods=["GET", "POST"])
def sales_order_info():

    # get the selected customer id from session
    # if there is no customer, we go back to create order page
    cid = session.get("sale_customer_id")
    if not cid:
        return redirect(url_for("sales_new"))

    # connect to database
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # get all branches to show them in the dropdown
    cur.execute("SELECT branch_id, nameBranch FROM branch ORDER BY branch_id")
    branches = cur.fetchall()

    # this variable will store the selected branch
    selected_branch_id = None

    # if the user submitted the branch form (post request)
    if request.method == "POST":
        selected_branch_id = request.form.get("branch_id")
    else:
        # if the branch is sent using url (get request)
        selected_branch_id = request.args.get("branch_id")

    # list to store staff of the selected branch
    staff = []

    # if a branch is selected
    if selected_branch_id:
        # get only cashier and branch manager of this branch
        cur.execute("""
            SELECT staff_id, first_name, last_name, positionStaff
            FROM staff
            WHERE branch_id = %s
              AND positionStaff IN ('Cashier', 'Branch Manager')
            ORDER BY staff_id
        """, (selected_branch_id,))
        staff = cur.fetchall()

    # close database connection
    cur.close()
    conn.close()

    # send branches, staff, and selected branch to the html page
    return render_template(
        "sales_order_info.html",
        branches=branches,
        staff=staff,
        selected_branch_id=selected_branch_id
    )

@app.route("/sales/create", methods=["POST"])
def sales_create():

    # get customer id from session
    cid = session.get("sale_customer_id")

    # if no customer is selected, go back to start
    if not cid:
        return redirect(url_for("sales_new"))

    # read order data from the form
    branch_id  = request.form.get("branch_id")
    staff_id   = request.form.get("staff_id")
    order_date = request.form.get("order_date")  # example: 2026-01-13T21:30

    # if any required data is missing, go back to order info page
    if not (branch_id and staff_id and order_date):
        return redirect(url_for("sales_order_info"))

    # convert html datetime format to mysql datetime format
    order_date_mysql = order_date.replace("T", " ") + ":00"

    # connect to database
    conn = get_connection()
    cur = conn.cursor()

    # insert new order into orders table
    cur.execute("""
        INSERT INTO orders (customer_id, staff_id, branch_id, order_date)
        VALUES (%s, %s, %s, %s)
    """, (cid, staff_id, branch_id, order_date_mysql))

    # save changes
    conn.commit()

    # get the id of the new order
    order_id = cur.lastrowid

    # close database connection
    cur.close()
    conn.close()

    # save order id in session for adding items later
    session["current_order_id"] = order_id

    # go to add items page
    return redirect(url_for("sales_items"))

#--------------------

@app.route("/sales/items")
def sales_items():
    # get current order id from session
    order_id = session.get("current_order_id")

    # if there is no order in session, go back to start new sale
    if not order_id:
        return redirect(url_for("sales_new"))

    # read any error message saved from previous add attempt
    # pop means: get it once then remove it
    error = session.pop("sale_error", None)

    # connect to database
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # get basic order info (customer + branch + staff)
    cur.execute("""
        SELECT o.order_id, o.order_date,
               c.first_name AS c_first, c.last_name AS c_last,
               b.nameBranch,
               s.first_name AS s_first, s.last_name AS s_last
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        JOIN branch b   ON o.branch_id   = b.branch_id
        JOIN staff s    ON o.staff_id    = s.staff_id
        WHERE o.order_id = %s
    """, (order_id,))
    order_info = cur.fetchone()

    # get products list for dropdown
    cur.execute("""
        SELECT product_id, product_name, unit_price
        FROM product
        ORDER BY product_name
    """)
    products = cur.fetchall()

    # get current items added to this order
    cur.execute("""
        SELECT oi.order_item_id, oi.quantity, oi.unit_price,
               p.product_name,
               (oi.quantity * oi.unit_price) AS subtotal
        FROM order_item oi
        JOIN product p ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
        ORDER BY oi.order_item_id
    """, (order_id,))
    items = cur.fetchall()

    # calculate total
    total = sum(float(x["subtotal"]) for x in items) if items else 0

    # close db
    cur.close()
    conn.close()

    # send everything to html (including error message)
    return render_template(
        "sales_items.html",
        order=order_info,
        products=products,
        items=items,
        total=total,
        error=error
    )


@app.route("/sales/items/add", methods=["POST"])
def sales_items_add():
    # get current order id from session
    order_id = session.get("current_order_id")

    # if no order, go back to start
    if not order_id:
        return redirect(url_for("sales_new"))

    # read form values
    product_id = request.form.get("product_id")
    qty = request.form.get("quantity")

    # basic validation
    if not product_id or not qty:
        session["sale_error"] = "please select a product and enter quantity."
        return redirect(url_for("sales_items"))

    qty = int(qty)
    if qty <= 0:
        session["sale_error"] = "quantity must be greater than 0."
        return redirect(url_for("sales_items"))

    # connect to database
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # get branch_id and staff_id for this order
    cur.execute("SELECT branch_id, staff_id FROM orders WHERE order_id = %s", (order_id,))
    o = cur.fetchone()
    branch_id = o["branch_id"]
    staff_id = o["staff_id"]

    # since each branch has one warehouse, get warehouse_id by branch_id
    cur.execute("SELECT warehouse_id FROM warehouse WHERE branch_id = %s LIMIT 1", (branch_id,))
    w = cur.fetchone()

    # if branch has no warehouse (should not happen), show message
    if not w:
        cur.close()
        conn.close()
        session["sale_error"] = "no warehouse found for this branch."
        return redirect(url_for("sales_items"))

    warehouse_id = w["warehouse_id"]

    # get product info (price + name)
    cur.execute("SELECT product_name, unit_price FROM product WHERE product_id = %s", (product_id,))
    p = cur.fetchone()

    if not p:
        cur.close()
        conn.close()
        session["sale_error"] = "product not found."
        return redirect(url_for("sales_items"))

    product_name = p["product_name"]
    unit_price = float(p["unit_price"])

    # check inventory for this product in this warehouse
    cur.execute("""
        SELECT inventory_id, stock_quantity
        FROM inventory
        WHERE product_id = %s AND warehouse_id = %s
        LIMIT 1
    """, (product_id, warehouse_id))
    inv = cur.fetchone()

    # if not in inventory at all
    if not inv:
        cur.close()
        conn.close()
        session["sale_error"] = f"'{product_name}' is not available in this branch inventory."
        return redirect(url_for("sales_items"))

    # if requested qty is more than available
    if inv["stock_quantity"] < qty:
        available = int(inv["stock_quantity"])
        cur.close()
        conn.close()
        session["sale_error"] = f"not enough stock for '{product_name}'-_- . available: {available} only ! "
        return redirect(url_for("sales_items"))

    # use a normal cursor for insert
    cur2 = conn.cursor()

    # insert order_item
    cur2.execute("""
        INSERT INTO order_item (order_id, product_id, warehouse_id, quantity, unit_price)
        VALUES (%s, %s, %s, %s, %s)
    """, (order_id, product_id, warehouse_id, qty, unit_price))

   
    # save changes
    conn.commit()

    # close db
    cur2.close()
    cur.close()
    conn.close()

    return redirect(url_for("sales_items"))



@app.route("/sales/items/delete/<int:order_item_id>", methods=["POST"])
def sales_items_delete(order_item_id):
    order_id = session.get("current_order_id")
    if not order_id:
        return redirect(url_for("sales_new"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # make sure item belongs to current order
    cur.execute("SELECT order_id FROM order_item WHERE order_item_id = %s", (order_item_id,))
    item = cur.fetchone()

    if not item or item["order_id"] != order_id:
        cur.close(); conn.close()
        return redirect(url_for("sales_items"))

    # delete 
    cur2 = conn.cursor()
    cur2.execute("DELETE FROM order_item WHERE order_item_id = %s", (order_item_id,))
    conn.commit()

    cur2.close()
    cur.close()
    conn.close()

    return redirect(url_for("sales_items"))




#---------

@app.route("/sales/checkout")
def sales_checkout():
    # get current order id from session
    order_id = session.get("current_order_id")
    if not order_id:
        return redirect(url_for("sales_new"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # calculate total from order_item table
    cur.execute("""
        SELECT SUM(quantity * unit_price) AS total
        FROM order_item
        WHERE order_id = %s
    """, (order_id,))

    row = cur.fetchone()
    total = row["total"]
    if total is None:
        total = 0
    cur.close()
    conn.close()
    # show checkout form (bill date + payment info)
    return render_template("sales_checkout.html", order_id=order_id, total=total)


@app.route("/sales/checkout/confirm", methods=["POST"])
def sales_checkout_confirm():
    # get current order id from session
    order_id = session.get("current_order_id")
    if not order_id:
        return redirect(url_for("sales_new"))

    # read checkout form values
    bill_date = request.form.get("bill_date")
    payment_method = request.form.get("payment_method")
    payment_status = request.form.get("payment_status")

    if not (bill_date and payment_method and payment_status):
        session["sale_error"] = "please fill bill date and payment details."
        return redirect(url_for("sales_checkout"))
    
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # get order_date + staff_id
    cur.execute("""
        SELECT order_date, staff_id
        FROM orders
        WHERE order_id = %s
    """, (order_id,))
    ord_row = cur.fetchone()

    if not ord_row:
        cur.close()
        conn.close()
        session["sale_error"] = "order not found."
        return redirect(url_for("sales_new"))

    order_date = ord_row["order_date"]  
    staff_id = ord_row["staff_id"]

    # get all items for this order
    cur.execute("""
        SELECT order_item_id, product_id, warehouse_id, quantity, unit_price
        FROM order_item
        WHERE order_id = %s
        ORDER BY order_item_id
    """, (order_id,))
    items = cur.fetchall()


    # if no items, do not allow checkout
    if not items:
        cur.close()
        conn.close()
        session["sale_error"] = "no items in this order. please add products first."
        return redirect(url_for("sales_items"))

    # calculate total from db items
    total = sum(float(it["quantity"]) * float(it["unit_price"]) for it in items)

    # check inventory for every item
    for it in items:
        pid = it["product_id"]
        wid = it["warehouse_id"]
        qty = int(it["quantity"])

        cur.execute("""
            SELECT stock_quantity
            FROM inventory
            WHERE product_id = %s AND warehouse_id = %s
            LIMIT 1
        """, (pid, wid))
        inv = cur.fetchone()
        # if product is missing or not enough stock
        if not inv:
            cur.close()
            conn.close()
            session["sale_error"] = "some items are not available in inventory anymore."
            return redirect(url_for("sales_items"))

        available = int(inv["stock_quantity"])
        if available < qty:
            # get product name for a friendly message
            cur.execute("SELECT product_name FROM product WHERE product_id = %s", (pid,))
            pr = cur.fetchone()
            pname = pr["product_name"] if pr else "this product"

            cur.close()
            conn.close()
            session["sale_error"] = f"checkout failed. not enough stock for '{pname}'. available: {available}"
            return redirect(url_for("sales_items"))

    # since all items are ok, apply updates (inventory + stock movement)
    cur2 = conn.cursor()

    for it in items:
        pid = it["product_id"]
        wid = it["warehouse_id"]
        qty = int(it["quantity"])

        # decrease inventory 
        cur2.execute("""
            UPDATE inventory
            SET stock_quantity = stock_quantity - %s,
                last_updated = %s
            WHERE product_id = %s AND warehouse_id = %s
            LIMIT 1
        """, (qty, order_date, pid, wid))

        # insert stock movement log 
        cur2.execute("""
            INSERT INTO stockMovment (movement_date, movement_type, product_id, warehouse_id, staff_id, qty_change)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (order_date, "SALE", pid, wid, staff_id, -qty))

    # finally create bill 
    cur2.execute("""
        INSERT INTO bill (order_id, bill_date, total_amount, payment_method, payment_status)
        VALUES (%s, %s, %s, %s, %s)
    """, (order_id, bill_date, total, payment_method, payment_status))

    conn.commit()
    bill_id = cur2.lastrowid

    cur2.close()
    cur.close()
    conn.close()

    # clear session to end the sale
    session.pop("current_order_id", None)
    session.pop("sale_customer_id", None)

    # show bill success page
    return render_template("sales_bill_success.html", bill_id=bill_id, order_id=order_id, total=total)

################################ veiwe orders (sales_orders.html)###############
@app.route("/sales/orders")
def sales_orders():
    # show orders list + items 
    q = request.args.get("q", "").strip()

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # get orders list
    sql = """
        SELECT
            o.order_id,
            o.order_date,
            c.first_name AS c_first,
            c.last_name  AS c_last,
            s.first_name AS s_first,
            s.last_name  AS s_last,
            b.nameBranch,

            (SELECT total_amount FROM bill WHERE order_id = o.order_id LIMIT 1) AS total_amount,
            (SELECT payment_status FROM bill WHERE order_id = o.order_id LIMIT 1) AS payment_status,
            (SELECT bill_id FROM bill WHERE order_id = o.order_id LIMIT 1) AS bill_id

        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        JOIN staff s    ON o.staff_id    = s.staff_id
        JOIN branch b   ON o.branch_id   = b.branch_id
    """

    params = []
    if q:
        sql += """
            WHERE
                o.order_id LIKE %s
                OR c.first_name LIKE %s
                OR c.last_name LIKE %s
                OR s.first_name LIKE %s
                OR s.last_name LIKE %s
        """
        like = f"%{q}%"
        params = [like, like, like, like, like]

    sql += " ORDER BY o.order_id ASC"

    cur.execute(sql, params)
    orders = cur.fetchall()

    # collect order ids to fetch all items
    order_ids = [o["order_id"] for o in orders]

    items_by_order = {}  # { order_id: [items...] }

    if order_ids:
        placeholders = ",".join(["%s"] * len(order_ids))

        cur.execute(f"""
            SELECT
                oi.order_id,
                oi.order_item_id,
                p.product_name,
                oi.quantity,
                oi.unit_price,
                (oi.quantity * oi.unit_price) AS subtotal
            FROM order_item oi
            JOIN product p ON oi.product_id = p.product_id
            WHERE oi.order_id IN ({placeholders})
            ORDER BY oi.order_id ASC, oi.order_item_id ASC
        """, tuple(order_ids))

        all_items = cur.fetchall()

        # group items under their order_id
        for it in all_items:
            oid = it["order_id"]
            if oid not in items_by_order:
                items_by_order[oid] = []
            items_by_order[oid].append(it)

    cur.close()
    conn.close()

    return render_template("sales_orders.html", orders=orders, items_by_order=items_by_order, q=q)



@app.route("/sales/today")
def sales_today():
    # this route shows only today's sales
    # it uses the same table and design as view orders

    # get today's date as string (yyyy-mm-dd)
    today_str = date.today().strftime("%Y-%m-%d")

    # connect to database
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # get orders where order_date is today
    cur.execute("""
        SELECT
            o.order_id,
            o.order_date,

            c.first_name AS c_first,
            c.last_name  AS c_last,

            s.first_name AS s_first,
            s.last_name  AS s_last,

            b.nameBranch,

            -- get bill info using subqueries (simple and allowed)
            (SELECT total_amount FROM bill WHERE order_id = o.order_id LIMIT 1) AS total_amount,
            (SELECT payment_status FROM bill WHERE order_id = o.order_id LIMIT 1) AS payment_status,
            (SELECT bill_id FROM bill WHERE order_id = o.order_id LIMIT 1) AS bill_id

        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        JOIN staff s    ON o.staff_id    = s.staff_id
        JOIN branch b   ON o.branch_id   = b.branch_id

        -- filter only today's orders
        WHERE DATE(o.order_date) = %s

        -- show orders in ascending order
        ORDER BY o.order_id ASC
    """, (today_str,))

    # fetch all today orders
    orders = cur.fetchall()

    # prepare dictionary to store items for each order
    items_by_order = {}

    # get order ids to fetch their items
    order_ids = [o["order_id"] for o in orders]

    if order_ids:
        # prepare placeholders for sql IN (...)
        placeholders = ",".join(["%s"] * len(order_ids))

        # get all items for today's orders
        cur.execute(f"""
            SELECT
                oi.order_id,
                oi.order_item_id,
                p.product_name,
                oi.quantity,
                oi.unit_price,
                (oi.quantity * oi.unit_price) AS subtotal
            FROM order_item oi
            JOIN product p ON oi.product_id = p.product_id
            WHERE oi.order_id IN ({placeholders})
            ORDER BY oi.order_id ASC, oi.order_item_id ASC
        """, tuple(order_ids))

        all_items = cur.fetchall()

        # group items by order_id
        for it in all_items:
            oid = it["order_id"]
            if oid not in items_by_order:
                items_by_order[oid] = []
            items_by_order[oid].append(it)

    # close database connection
    cur.close()
    conn.close()

    # render the same orders page but with today title and description
    return render_template(
        "sales_orders.html",
        orders=orders,
        items_by_order=items_by_order,
        q="",
        page_title="Today Sales",
        page_desc="view sales orders created today."
    )


###################### ###########################################
###################### product  sidebar ###########################################
#############################################################3

@app.route("/products")
def products_list():

    # get filters from url
    branch_id     = request.args.get("branch_id", "").strip()
    supplier_id   = request.args.get("supplier_id", "").strip()
    product_name  = request.args.get("product_name", "").strip()
    status = request.args.get("status", "").strip()

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # base query
    query = """
        SELECT
            p.product_name,
            c.nameCat,
            p.sku,
            s.supplier_name,
            b.nameBranch,
            w.name_warehouse,
            i.stock_quantity,
            MAX(pd.arrival_date) AS last_entry_date
        FROM product p
        JOIN category c ON p.category_id = c.category_id
        JOIN supplier s ON p.supplier_id = s.supplier_id
        JOIN inventory i ON p.product_id = i.product_id
        JOIN warehouse w ON i.warehouse_id = w.warehouse_id
        JOIN branch b ON w.branch_id = b.branch_id
        JOIN purchasedetail pd ON p.product_id = pd.product_id
    """

    conditions = []
    params = []

    # filter by branch (optional)
    if branch_id and branch_id.isdigit():
        conditions.append("b.branch_id = %s")
        params.append(int(branch_id))

    # filter by supplier (optional)
    if supplier_id and supplier_id.isdigit():
        conditions.append("s.supplier_id = %s")
        params.append(int(supplier_id))

    # filter by product name (optional)
    if product_name:
        conditions.append("p.product_name LIKE %s")
        params.append(f"%{product_name}%")

    # filter by status (optional)
    if status == "available":
        conditions.append("i.stock_quantity > 10")
    elif status == "low":
        conditions.append("i.stock_quantity BETWEEN 1 AND 10")
    elif status == "out":
        conditions.append("i.stock_quantity = 0")


    # add conditions if exist
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # group + sort
    query += """
        GROUP BY
            p.product_id,
            p.product_name,
            c.nameCat,
            p.sku,
            s.supplier_name,
            b.nameBranch,
            w.name_warehouse,
            i.stock_quantity
        ORDER BY
            c.nameCat ASC,
            last_entry_date DESC
   
    """

    # run query
    cur.execute(query, params)
    products = cur.fetchall()

    # dropdown lists
    cur.execute("SELECT branch_id, nameBranch FROM branch ORDER BY nameBranch")
    branches = cur.fetchall()

    cur.execute("SELECT supplier_id, supplier_name FROM supplier ORDER BY supplier_name")
    suppliers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "products_list.html",
        products=products,
        branches=branches,
        suppliers=suppliers,
        filters={
            "branch_id": branch_id,
            "supplier_id": supplier_id,
            "product_name": product_name,
            "status": status

        }
    )


##############################################################################################################################################

###################              ###             stock-movements              #################           ###          ###

###############################################################################################################################################3

@app.route("/stock/movements/log")
def stock_movements_log():
    warehouse_id   = request.args.get("warehouse_id", "").strip()
    movement_type  = request.args.get("movement_type", "").strip()
    date_from      = request.args.get("date_from", "").strip()
    date_to        = request.args.get("date_to", "").strip()

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT sm.movement_id,sm.movement_date,sm.movement_type,sm.qty_change,p.product_name,p.sku,w.name_warehouse,s.first_name,s.last_name,s.positionStaff
        FROM stockMovment sm
        JOIN product p ON sm.product_id = p.product_id
        JOIN warehouse w ON sm.warehouse_id = w.warehouse_id
        JOIN staff s ON sm.staff_id = s.staff_id
    """

    conditions = []
    params = []

    if warehouse_id and warehouse_id.isdigit():
        conditions.append("sm.warehouse_id = %s")
        params.append(int(warehouse_id))

    if movement_type:
        conditions.append("sm.movement_type = %s")
        params.append(movement_type)

    if date_from:
        conditions.append("DATE(sm.movement_date) >= %s")
        params.append(date_from)

    if date_to:
        conditions.append("DATE(sm.movement_date) <= %s")
        params.append(date_to)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY sm.movement_date DESC LIMIT 200"

    cur.execute(query, params)
    movements = cur.fetchall()

    cur.execute("SELECT warehouse_id, name_warehouse FROM warehouse ORDER BY name_warehouse")
    warehouses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "stock_movements_log.html",
        movements=movements,
        warehouses=warehouses,
        filters={ "warehouse_id": warehouse_id, "movement_type": movement_type, "date_from": date_from, "date_to": date_to }
    )

############################################################################
######################  productsReports  sidebar ###########################################
############################################################################



def get_month_range(month_value):
    # ----------------------------------------------------------
    # 
    #   return (start_date, end_date, month_string)
    #   - if user chooses a month: use it
    #   - if user does not choose: default to LAST month
    #
    # month_value format: "yyyy-mm"
    # start: first day of month (inclusive)
    # end: first day of next month (exclusive)
    # ----------------------------------------------------------

    if month_value and len(month_value) == 7 and month_value[4] == "-":
        # parse user month
        y = int(month_value[:4])
        m = int(month_value[5:7])
         #start date = first day in that month
        start = datetime(y, m, 1)
        # end date = first day of next month
        end = datetime(y + 1, 1, 1) if m == 12 else datetime(y, m + 1, 1)
        #return start/end + same month string (for keeping filter in UI)
        return start, end, month_value

    #  if month_value is empty -> default to last month
    today = datetime.now()
    this_month_start = datetime(today.year, today.month, 1)
    end = this_month_start

    if today.month == 1:
        # if we are in january -> last month is december of last year
        start = datetime(today.year - 1, 12, 1)
    else:
        start = datetime(today.year, today.month - 1, 1)
    # return start/end + formatted month string 
    return start, end, start.strftime("%Y-%m")


@app.route("/reports/sales-products")
def report_sales_products():

    # ==========================================================
    # 1)read filters from url 
    # ==========================================================
    branch_id   = request.args.get("branch_id", "").strip()     # branch filter (optional)
    month       = request.args.get("month", "").strip()         # month filter (yyyy-mm)
    category_id = request.args.get("category_id", "").strip()   # category filter for query 8
    days        = request.args.get("days", "10").strip()        # days filter for query 15 (default 10)

    # 2)sanitize days (make sure it is a valid positive number)
    days = int(days) if days.isdigit() else 10                  # if user input is not a number -> use 10
    if days < 1:
        days = 1                                                # avoid 0 or negative days

    # ==========================================================
    # 3) convert month filter to start/end dates
    # ==========================================================
    start, end, month_fixed = get_month_range(month)            

    ## ==========================================================
    # 4) connect to database
    # ==========================================================
    conn = get_connection()                                    
    cur = conn.cursor(dictionary=True) # results as dictionaries 


    # ==========================================================
    # 5) load dropdown lists (branch + category)
    # ==========================================================
    cur.execute("select branch_id, nameBranch from branch order by nameBranch")
    branches = cur.fetchall()                                  

    cur.execute("select category_id, nameCat from category order by nameCat")
    categories = cur.fetchall()                                

    # ==========================================================
    # query 9: top 3 bestselling products in the selected month
    #  sum(order_item.quantity) grouped by product
    #   
    # ==========================================================

    query9 = """
        select
          p.product_id,
          p.product_name,
          sum(oi.quantity) as total_qty
        from order_item oi
        join orders o  on o.order_id = oi.order_id
        join product p on p.product_id = oi.product_id
        where o.order_date >= %s and o.order_date < %s
    """

    # params for month range
    params9 = [
        start.strftime("%Y-%m-%d %H:%M:%S"),                     
        end.strftime("%Y-%m-%d %H:%M:%S")                        
    ]

    # optional: if the user selected a branch -> filter sales by that branch
    if branch_id and branch_id.isdigit():
        query9 += " and o.branch_id = %s"                        # add another condition
        params9.append(int(branch_id))                           # add value for the new %s

    # group by product and take the top 3 (highest total qty)
    query9 += """
        group by p.product_id, p.product_name
        order by total_qty desc
        limit 3
    """

    cur.execute(query9, params9)                                 # run query 9
    top3 = cur.fetchall()                                        # list of results

    # ==========================================================
    # query 8: best-selling product in a selected category
    # highest sum(quantity) inside a category
    # ==========================================================

    best_in_category = None                                      # default: no category selected or no result

    if category_id and category_id.isdigit():

        query8 = """
            select
              p.product_id,
              p.product_name,
              c.nameCat as category,
              sum(oi.quantity) as total_qty
            from order_item oi
            join orders o   on o.order_id = oi.order_id
            join product p  on p.product_id = oi.product_id
            join category c on c.category_id = p.category_id
            where p.category_id = %s
              and o.order_date >= %s
              and o.order_date <  %s
        """

        # params for query8: category + month range
        params8 = [
            int(category_id),                                    
            start.strftime("%Y-%m-%d %H:%M:%S"),                  
            end.strftime("%Y-%m-%d %H:%M:%S")                     
        ]

        # optional: branch filter 
        if branch_id and branch_id.isdigit():
            query8 += " and o.branch_id = %s"
            params8.append(int(branch_id))

        # group by products, order by total qty, take only the best one
        query8 += """
            group by p.product_id, p.product_name, c.nameCat
            order by total_qty desc
            limit 1
        """

        cur.execute(query8, params8)                              # run query 8
        best_in_category = cur.fetchone()                         # single row (best product) or None

    # ==========================================================
    # query 15: products not sold in last n days
    # product is returned if there is NO order_item for it
    #        with order_date >= cutoff
    # 
    # ==========================================================

    # build cutoff date 
    cutoff = datetime.now() - timedelta(days=days)               # now minus n days
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")            # convert to string for mysql

    query15 = """
        select
          p.product_id,
          p.product_name,
          p.sku,
          c.nameCat as category
        from product p
        join category c on c.category_id = p.category_id
        where not exists (
          select *
          from order_item oi
          join orders o on o.order_id = oi.order_id
          where oi.product_id = p.product_id
            and o.order_date >= %s
    """

    # first param is always cutoff date
    params15 = [cutoff_str]

    # if branch is selected, check "not sold" inside that branch only
    if branch_id and branch_id.isdigit():
        query15 += " and o.branch_id = %s"
        params15.append(int(branch_id))

    # close not exists + order results
    query15 += """
        )
        order by p.product_name
        
    """

    cur.execute(query15, params15)                               # run query 15
    not_sold = cur.fetchall()                                    # list of products not sold
    not_sold_count = len(not_sold)                               # count for badge in ui

    # 6) close database connection
    cur.close()                                                  # close cursor
    conn.close()                                                 # close connection

    # ==========================================================
    # 7) send results to html
    # ==========================================================

    return render_template(
        "report_sales_products.html",
        branches=branches,                                       # for branch dropdown
        categories=categories,                                   # for category dropdown
        top3=top3,                                               # result of query 9
        best_in_category=best_in_category,                       # result of query 8
        not_sold=not_sold,                                       # result of query 15
        not_sold_count=not_sold_count,                           # count for query 15
        filters={
            "branch_id": branch_id,                              # keep selected branch in ui
            "category_id": category_id,                          # keep selected category in ui
            "month": month_fixed,                                # keep month in ui
            "days": str(days)                                    # keep days in ui
        }
    )



###########################################################################
######################  branch reports  sidebar ###########################################
###########################################################################


@app.route("/reports/sales-branches")
def report_sales_branches():

    # 1) read filter from url     
    month     = request.args.get("month", "").strip()           

    # 2) build month range for the selected month
    start, end, month_fixed = get_month_range(month)             

    # 3) connect to database
    conn = get_connection()                                    
    cur = conn.cursor(dictionary=True)                         

    
    # ==========================================================
    # query 7: total sales revenue for each branch in given month
    #  sum(order_item.quantity * order_item.unit_price)
    # ==========================================================

    query7 = """
        select
          b.branch_id,
          b.nameBranch as branch_name,
          sum(oi.quantity * oi.unit_price) as revenue
        from orders o
        join order_item oi on oi.order_id = o.order_id
        join branch b on b.branch_id = o.branch_id
        where o.order_date >= %s and o.order_date < %s
    """

    params7 = [
        start.strftime("%Y-%m-%d %H:%M:%S"),                      # month start
        end.strftime("%Y-%m-%d %H:%M:%S")                         # month end
    ]

    
    # group by branch to get revenue per branch
    query7 += """
        group by b.branch_id, b.nameBranch
        order by revenue desc
    """

    cur.execute(query7, params7)                                  # run query 7
    revenue_by_branch = cur.fetchall()                             # list of branches + revenue

    # ==========================================================
    # query 13: monthly sales summary for each branch
    #  orders count + total qty + total revenue
    # ==========================================================

    query13 = """
        select
          b.branch_id,
          b.nameBranch as branch_name,
          count(distinct o.order_id) as orders_count,
          sum(oi.quantity) as total_qty,
          sum(oi.quantity * oi.unit_price) as total_revenue
        from orders o
        join order_item oi on oi.order_id = o.order_id
        join branch b on b.branch_id = o.branch_id
        where o.order_date >= %s and o.order_date < %s
    """

    params13 = [
        start.strftime("%Y-%m-%d %H:%M:%S"),                       # month start
        end.strftime("%Y-%m-%d %H:%M:%S")                          # month end
    ]

    
    # group by branch to get one summary row per branch
    query13 += """
        group by b.branch_id, b.nameBranch
        order by total_revenue desc
    """

    cur.execute(query13, params13)                                 # run query 13
    monthly_summary = cur.fetchall()                               # list of summary rows

    # calculate total revenue (sum of all branches)
    total_revenue = sum(r["revenue"] or 0 for r in revenue_by_branch)

    # calculate total orders (sum of orders_count across branches)
    total_orders = sum(s["orders_count"] or 0 for s in monthly_summary)

    # ==========================================================
    # query 14: branch with the highest sales revenue in last month
    #sum(qty*price) for previous month only
    # ==========================================================

    # build last month range 
    today = datetime.now()                                         # current datetime
    first_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = first_this_month                               # exclusive end for last month
    last_month_start = (first_this_month - timedelta(days=1)).replace(day=1)  # first day of last month

    query14 = """
        select
          b.branch_id,
          b.nameBranch as branch_name,
          sum(oi.quantity * oi.unit_price) as revenue
        from orders o
        join order_item oi on oi.order_id = o.order_id
        join branch b on b.branch_id = o.branch_id
        where o.order_date >= %s and o.order_date < %s
        group by b.branch_id, b.nameBranch
        order by revenue desc
        limit 1
    """

    params14 = [
        last_month_start.strftime("%Y-%m-%d %H:%M:%S"),             # last month start
        last_month_end.strftime("%Y-%m-%d %H:%M:%S")                # last month end
    ]

    cur.execute(query14, params14)                                  # run query 14
    best_branch_last_month = cur.fetchone()                          # one row (or None)

    # 5) close database
    cur.close()                                                      # close cursor
    conn.close()                                                     # close connection

    # 6) render the report page
    return render_template(
        "report_sales_branches.html",
        revenue_by_branch=revenue_by_branch,                         # query 7
        monthly_summary=monthly_summary,                             # query 13
        best_branch_last_month=best_branch_last_month,               # query 14
        total_revenue=total_revenue,
        total_orders=total_orders,
        filters={
            "month": month_fixed                                     
        },
        last_month_label=last_month_start.strftime("%B %Y")         
    )






########################################################     DELETE     ###############################################################
@app.route("/customers/delete", methods=["GET", "POST"])
def delete_customer_search():
    if request.method == "POST":
        # when user searches by ID
        customer_id = request.form["customer_id"].strip()

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
        customer = cur.fetchone()
        
        cur.close()
        conn.close()
        
        
        if not customer:
            return render_template("delete_customer.html", error="Customer ID not found.")
        else:
         return render_template("delete_confirm.html", customer=customer) # show confirmation page
        
    else:
      return render_template("delete_customer.html")


@app.route("/customers/delete/confirm", methods=["POST"])
def delete_customer_confirm():
    customer_id = request.form["customer_id"].strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM customer WHERE customer_id = %s", (customer_id,))
    conn.commit()
    cur.close()
    conn.close()

    return render_template("successDelete.html", message="Customer deleted successfully!")

############################################################### update ###################################################################
@app.route("/customers/update", methods=["GET", "POST"])
def update_customer_search():
    if request.method == "POST":
        customer_id = request.form["customer_id"].strip()

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
        customer = cur.fetchone()
        cur.close()
        conn.close()

        if not customer:
            return render_template("update_customer.html", error="Customer ID not found.")
        else:
         return render_template("update_form.html", customer=customer)
        
    else:
     return render_template("update_customer.html")


@app.route("/customers/update/confirm", methods=["POST"])
def update_customer_confirm(): # read updated data
    customer_id = request.form["customer_id"].strip()
    first_name = request.form["first_name"].strip()
    last_name  = request.form["last_name"].strip()
    email      = request.form["email"].strip()
    phone      = request.form["phone"].strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(" UPDATE customer  SET first_name=%s, last_name=%s, email=%s, phone=%s  WHERE customer_id=%s",(first_name, last_name, email, phone, customer_id) )
    conn.commit()
    cur.close()
    conn.close()

    return render_template("update_success.html")







##########################################################################################################################################################################
##########################################################################################################################################################################
##########################################################################################################################################################################
##########################################################################################################################################################################
################################################################# (NEW PURCHASE) #########################################################################################
##########################################################################################################################################################################
##########################################################################################################################################################################
##########################################################################################################################################################################
##########################################################################################################################################################################
##########################################################################################################################################################################
@app.route("/purchases/suppliers", methods=["GET"])
def purchases_suppliers_pick():

    phone = request.args.get("phone", "").strip()
    suppliers = []

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if phone:
        cur.execute(
            """
            select supplier_id, supplier_name, contact_phone, email
            from supplier
            where contact_phone = %s
            order by supplier_name
            """,(phone,)
        )
    else:
        cur.execute(
            """
            select supplier_id, supplier_name, contact_phone, email
            from supplier
            order by supplier_name
            """
        )
    suppliers = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("purchases/supplier_select.html", suppliers=suppliers)

###############################                                                      ###############################
#                                            AFTER SELECT SUPPLIER
################################                                                        ###############################
@app.route("/suppliers/use/<int:supplier_id>", methods=["GET"])
def set_supplier_for_purchase(supplier_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""select 1 
                from supplier 
                where supplier_id = %s""", (supplier_id,))
    exists = cur.fetchone()
    cur.close()
    conn.close()

    if not exists:
        return redirect("/purchases/suppliers")

    session["purchase_supplier_id"] = supplier_id
    return redirect("/purchases/new")



@app.route("/purchases/new", methods=["GET"])
def purchase_step1_supplier():
    sid = session.get("purchase_supplier_id")  #after do session (USE)
    supplier = None
    if sid:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""select * 
                       from supplier 
                       where supplier_id = %s
                       """, (sid,))
        supplier = cur.fetchone()
        cur.close()
        conn.close()

        if not supplier:
            session.pop("purchase_supplier_id", None)  # We stored it in session cause we need it after ........

    return render_template("purchases/purchase_supplier.html", supplier=supplier)



###############################                                                         ###############################
#                                            ADD supplier
################################                                                        ###############################
@app.route("/suppliers/new", methods=["GET", "POST"])
def create_supplier():

    if request.method == "POST":
        supplier_name  = request.form["supplier_name"].strip()
        contact_name   = request.form["contact_name"].strip()
        contact_phone  = request.form["contact_phone"].strip()
        email          = request.form["email"].strip()
        address        = request.form["address"].strip()

        conn = get_connection()
        cur = conn.cursor()
         
         #check if phone already exist 
        cur.execute("""select supplier_id 
                    from supplier 
                    where contact_phone = %s""",(contact_phone,))
        existing = cur.fetchone()
        if existing:
            cur.close()
            conn.close()
            return render_template("suppliers/supplier_form.html",error="Supplier with this phone number already exists.",from_param=request.form.get("from", ""))
        #insert
        cur.execute(
            "INSERT INTO supplier (supplier_name, contact_name, contact_phone, email, address) VALUES (%s, %s, %s, %s, %s)",
            (supplier_name, contact_name, contact_phone, email, address)
        )
        conn.commit()
        cur.close()
        conn.close()

        if request.form.get("from") == "purchase":
            if contact_phone:
                return redirect("/purchases/suppliers")
       

        return redirect("/purchases/suppliers")

    else:
        from_param = request.args.get("from", "").strip()
        return render_template("suppliers/supplier_form.html", from_param=from_param)
    

###############################                                                      ###############################
#                                    purchase_step2_header
################################                                                        ###############################

@app.route("/purchases/header", methods=["GET", "POST"])
def purchase_step2_header():
    sid = session.get("purchase_supplier_id")
    if not sid:
        return redirect("/purchases/new")

    if request.method == "GET":
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("""select * 
                    from supplier 
                    where supplier_id=%s""", (sid,))
        supplier = cur.fetchone()

        cur.execute("""select branch_id, nameBranch 
                    from branch 
                    order by nameBranch""")
        branches = cur.fetchall()

        cur.close()
        conn.close()

        return render_template("purchases/purchase_header.html",supplier=supplier,branches=branches,error=None,purchase_date=None,invoice_number=None,branch_id=None,staff_phone=None )

    # POST
    purchase_date  = request.form.get("purchase_date", "").strip()
    invoice_number = request.form.get("invoice_number", "").strip()
    branch_id      = request.form.get("branch_id", "").strip()
    staff_phone    = request.form.get("staff_phone", "").strip()

    if not purchase_date or not branch_id.isdigit() or not staff_phone:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("""select * 
                    from supplier 
                    where supplier_id=%s""", (sid,))
        supplier = cur.fetchone()

        cur.execute("""select branch_id, nameBranch 
                    from branch 
                    order by nameBranch""")
        branches = cur.fetchall()

        cur.close()
        conn.close()

        return render_template("purchases/purchase_header.html",supplier=supplier,branches=branches,
            error="Please fill all required fields (date, branch, staff phone).",purchase_date=purchase_date,
            invoice_number=invoice_number,branch_id=branch_id,staff_phone=staff_phone )

    branch_id = int(branch_id)

    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur2 = conn.cursor()

    cur.execute("""
        select staff_id
        from staff
        where phone=%s and branch_id=%s
        LIMIT 1
    """, (staff_phone, branch_id))
    st = cur.fetchone()

    if not st:
        cur.execute("""select * 
                    from supplier 
                    where supplier_id=%s""", (sid,))
        supplier = cur.fetchone()
        cur.execute("""select branch_id, nameBranch 
                    from branch
                     order by nameBranch""")
        branches = cur.fetchall()

        cur.close()
        cur2.close()
        conn.close()

        return render_template("purchases/purchase_header.html",supplier=supplier,branches=branches,error="Staff phone not found for this branch. Please enter a valid employee phone.",
            purchase_date=purchase_date, invoice_number=invoice_number, branch_id=branch_id, staff_phone=staff_phone )

    staff_id = st["staff_id"]

    session["purchase_branch_id"] = branch_id
    session["purchase_staff_id"]  = staff_id

    purchase_id = session.get("purchase_id")

    if not purchase_id:
        cur2.execute("""
       INSERT INTO purchase (supplier_id, branch_id, staff_id, purchase_date, invoice_number, total_amount)
       VALUES (%s, %s, %s, %s, %s, 0)
        """, (sid, branch_id, staff_id, purchase_date, invoice_number if invoice_number else None))

        conn.commit()
        session["purchase_id"] = cur2.lastrowid
    else:
        cur2.execute("""
             update purchase
             set branch_id=%s, staff_id=%s, purchase_date=%s, invoice_number=%s
             where purchase_id=%s
         """, (branch_id, staff_id, purchase_date, invoice_number if invoice_number else None, purchase_id))
        conn.commit()

    cur.close()
    cur2.close()
    conn.close()

    return redirect("/purchases/items")





###############################                                                      ###############################
#                                    purchases enter items
################################                                                        ###############################
@app.route("/purchases/items", methods=["GET"])
def purchase_step3_items():
    purchase_id = session.get("purchase_id")
    sid = session.get("purchase_supplier_id")
    branch_id = session.get("purchase_branch_id")

    if not purchase_id or not sid or not branch_id:
        return redirect("/purchases/new")

 
    search = request.args.get("search", "").strip()
    error = request.args.get("error", "").strip() or None
    product_results = []

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # supplier_name
    cur.execute("""select supplier_name 
                from supplier
                 where supplier_id=%s""", (sid,))
    r = cur.fetchone()
    supplier_name = r["supplier_name"] if r else ""

    # branch_name
    cur.execute("""select nameBranch
                 from branch
                 where branch_id=%s""", (branch_id,))
    r = cur.fetchone()
    branch_name = r["nameBranch"] if r else ""

    #  SEARCH products 
    if search:
        like = f"%{search}%"
        cur.execute("""
            select product_id, product_name, sku, unit_price, purchase_price
            from product
            where product_name like %s or sku like %s
            order by product_name
            LIMIT 50
        """, (like, like))
        product_results = cur.fetchall()

    # items in this purchase  
    cur.execute("""
        select pd.purchaseDetail_id,p.product_name,pd.quantity,pd.unit_cost,(pd.quantity * pd.unit_cost) AS subtotal
        from purchasedetail pd join product p on p.product_id = pd.product_id
        where pd.purchase_id = %s
        order by pd.purchaseDetail_id
    """, (purchase_id,))
    items = cur.fetchall()

    cur.execute("""
        select sum(quantity * unit_cost) AS total
        from purchasedetail
        where purchase_id = %s
    """, (purchase_id,))
    r = cur.fetchone()
    total_amount = f"{(r['total'] or 0):.2f}"

    cur.close()
    conn.close()

    return render_template("purchases/purchase_items.html",purchase_id=purchase_id,supplier_name=supplier_name,branch_name=branch_name,search=search,
        product_results=product_results,items=items,total_amount=total_amount,error=error)


##############################################################################################################################################

###################                      ###                New Product            #################           ###          ###

###############################################################################################################################################3

@app.route("/products/new", methods=["GET", "POST"])
def product_new():
    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        sku          = request.form.get("sku", "").strip()
        category_id  = request.form.get("category_id", "").strip()
        supplier_id  = request.form.get("supplier_id", "").strip()
        description  = request.form.get("product_description", "").strip()
        purchase_price = request.form.get("purchase_price", "").strip()
        unit_price     = request.form.get("unit_price", "").strip()


        back = request.form.get("back", "/products").strip()
        from_param = request.form.get("from_param", "").strip()

        if not product_name or not unit_price or not category_id.isdigit() or not supplier_id.isdigit() or not purchase_price.isdigit():
            return redirect(f"/products/new?from={from_param}&back={back}&error=Missing+required+fields")

        try:
            price = float(unit_price)
        except:
            return redirect(f"/products/new?from={from_param}&back={back}&error=Invalid+price")

        conn = get_connection()
        cur = conn.cursor()

        #insert product
        try:
            cur.execute("""
                INSERT INTO product (product_name, category_id, supplier_id, sku, product_description, purchase_price,unit_price)
                VALUES (%s, %s, %s, %s, %s, %s,%s)
            """, (product_name, int(category_id), int(supplier_id), sku if sku else None, description, purchase_price,price))

            conn.commit()
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            return redirect(f"/products/new?from={from_param}&back={back}&error=SKU+or+data+already+exists")

        cur.close()
        conn.close()

        return redirect(back)

    else:
        back = request.args.get("back", "/products").strip()
        from_param = request.args.get("from", "").strip()
        error = request.args.get("error", "").strip() or None

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("""select category_id, nameCat 
                    from category 
                    order by nameCat""")
        categories = cur.fetchall()

        cur.execute("""select supplier_id, supplier_name 
                    from supplier 
                    order by supplier_name""")
        suppliers = cur.fetchall()

        cur.close()
        conn.close()

        return render_template("products/product_form.html",back=back,from_param=from_param,categories=categories,suppliers=suppliers,error=error)
#################################




##############################################################################################################################################

###################              ###             Add items to Purchase            #################           ###          ###

###############################################################################################################################################3
from urllib.parse import quote

@app.route("/purchases/items/add", methods=["POST"])
def purchase_add_item():
   
    purchase_id = session.get("purchase_id")
    branch_id   = session.get("purchase_branch_id")
    last_search = request.form.get("last_search", "").strip()

    def back(msg=None):
        base = "/purchases/items"
        qs = []
        if last_search:
            qs.append("search=" + quote(last_search))
        if msg:
            qs.append("error=" + quote(msg))
        return redirect(base + ("?" + "&".join(qs) if qs else ""))

    if not purchase_id or not branch_id:
        return back("Purchase session missing. Please re-enter Step 2.")

    product_id_str = request.form.get("product_id", "").strip()
    qty_str        = request.form.get("quantity", "").strip()

    if not product_id_str.isdigit() or not qty_str.isdigit():
        return back("Invalid product or quantity.")

    product_id = int(product_id_str)
    quantity   = int(qty_str)
    if quantity <= 0:
        return back("Quantity must be >= 1.")

    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
# Warehouse
    try:
        cur.execute("""
            SELECT warehouse_id, capacity
            FROM warehouse
            WHERE branch_id=%s
            LIMIT 1
        """, (branch_id,))
        w = cur.fetchone()
        if not w:
            return back("No warehouse for this branch.")
        warehouse_id = w["warehouse_id"]

# purchase_price = unit_cost
        cur.execute("""select purchase_price
                     from product 
                    where product_id=%s""", (product_id,))
        p = cur.fetchone()
        if not p:
            return back("Product not found.")
        unit_cost = float(p["purchase_price"] or 0)


        if unit_cost <= 0:
            return back("Purchase price not set for this product")

        # add/update
        cur.execute("""
            select purchaseDetail_id
            from purchasedetail
            where purchase_id=%s and warehouse_id=%s and product_id=%s
            LIMIT 1
        """, (purchase_id, warehouse_id, product_id))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                update purchasedetail
                set quantity = quantity + %s, unit_cost = %s
                where purchaseDetail_id = %s
            """, (quantity, unit_cost,  existing["purchaseDetail_id"]))
        else:
            cur.execute("""
                insert into purchasedetail (purchase_id, warehouse_id, product_id, quantity, unit_cost,received_qty, arrival_date, statusP)
                values (%s, %s, %s, %s,%s, 0,NULL,'Ordered')
            """, (purchase_id, warehouse_id, product_id, quantity, unit_cost))

        conn.commit()
        return back()

    except Exception as e:
        conn.rollback()
        return back("Failed to add item.")

    finally:
        cur.close()
        conn.close()


 ############################# cLEAR  ############################################################
@app.route("/dev/clear-session")
def clear_session():
    session.clear()
    return "Session cleared"
 ###################################################################################


 ############################# D E L E T E ############################################################

@app.route("/purchases/items/delete/<int:purchaseDetail_id>", methods=["POST"])
def purchase_delete_item(purchaseDetail_id):
    purchase_id = session.get("purchase_id")
    if not purchase_id:
        return redirect("/purchases/new")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        delete from purchasedetail
        where purchaseDetail_id=%s and purchase_id=%s
    """, (purchaseDetail_id, purchase_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/purchases/items")



##############################################################################################################################################

###################              ###             Finish  purchase             #################           ###          ###

###############################################################################################################################################3
@app.route("/purchases/finish/confirm", methods=["POST"])
def purchase_finish_execute():
    purchase_id = session.get("purchase_id")
    branch_id   = session.get("purchase_branch_id")
    sid         = session.get("purchase_supplier_id")
    staff_id    = session.get("purchase_staff_id")   
    
    if not purchase_id or not branch_id or not sid:
        return redirect("/purchases/new")
    if not staff_id:
        return redirect("/purchases/header")
    
    conn = get_connection()
    cur = conn.cursor(dictionary=True) 
    
    # Get warehouse_id
    cur.execute("""select warehouse_id 
                from warehouse 
                where branch_id=%s""", (branch_id,))
    w = cur.fetchone()
    if not w:
        cur.close()
        conn.close()
        return redirect("/purchases/items")
    warehouse_id = w["warehouse_id"]
    
    # Get items
    cur.execute("""
        select purchaseDetail_id, product_id, quantity, unit_cost
        from purchasedetail
        where purchase_id = %s
    """, (purchase_id,))
    items = cur.fetchall()
    
    if len(items) == 0:
        cur.close()
        conn.close()
        return redirect("/purchases/items")
    
    # calculate total
    cur.execute("""
        select sum(quantity * unit_cost) AS total
        from purchasedetail
        where purchase_id = %s
    """, (purchase_id,))
    row = cur.fetchone()
    total_amount = row["total"] if row and row["total"] is not None else 0.0
    
    # Update purchase total
    cur.execute("""
        update purchase
        set total_amount = %s
        where purchase_id = %s
    """, (total_amount, purchase_id))

    # Commit all changes at once
    conn.commit()
    cur.close()
    conn.close()
    
    finished_purchase_id = purchase_id
    
    # clean session
    session.pop("purchase_id", None)
    session.pop("purchase_supplier_id", None)
    session.pop("purchase_branch_id", None)
    session.pop("purchase_staff_id", None)   
    
    return redirect(f"/purchases/view/{finished_purchase_id}")

##############################################################################################################################################

###################              ###             Receive             #################           ###          ###

###############################################################################################################################################
@app.route("/purchases/receive/<int:purchase_id>", methods=["GET"])
def purchase_receive_page(purchase_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # header
    cur.execute("""
        select p.purchase_id, p.purchase_date, p.total_amount, s.supplier_name, b.nameBranch
        from purchase p join supplier s on s.supplier_id = p.supplier_id join branch b on b.branch_id = p.branch_id
        where p.purchase_id=%s
    """, (purchase_id,))
    purchase = cur.fetchone()
    if not purchase:
        cur.close(); conn.close()
        return redirect("/purchases")

    # items
    cur.execute("""
        select pd.purchaseDetail_id, pr.product_name,pd.quantity AS ordered_qty,pd.received_qty,pd.unit_cost,pd.statusP
        from purchasedetail pd join product pr on pr.product_id = pd.product_id
        where pd.purchase_id=%s
        order by pd.purchaseDetail_id
    """, (purchase_id,))
    items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("purchases/purchase_receive.html", purchase=purchase, items=items, error=None)


##############################################################################################################################################

###################              ###             Receive Confirm             #################           ###          ###

###############################################################################################################################################
@app.route("/purchases/recive/confirm", methods=["POST"])
def purchase_receive_confirm():
    purchase_id_str = request.form.get("purchase_id", "").strip()
    if not purchase_id_str.isdigit():
        return redirect("/purchases")
    purchase_id = int(purchase_id_str)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            select branch_id, staff_id
            from purchase
            where purchase_id=%s
        """, (purchase_id,))
        row = cur.fetchone()
        if not row:
            return redirect("/purchases")

        branch_id = row["branch_id"]
        staff_id  = row["staff_id"]

        if not staff_id:
            return redirect(f"/purchases/receive/{purchase_id}?error=" + quote("Purchase has no staff_id."))

        # warehouse + capacity
        cur.execute("""
            select warehouse_id, capacity
            from warehouse
            where branch_id=%s
            LIMIT 1
        """, (branch_id,))
        w = cur.fetchone()
        if not w:
            return redirect(f"/purchases/receive/{purchase_id}?error=" + quote("No warehouse."))

        warehouse_id = w["warehouse_id"]
        capacity     = int(w["capacity"] or 0)

        # current stock
        cur.execute("""
            SELECT SUM(stock_quantity) AS s
            FROM inventory
            WHERE warehouse_id=%s
        """, (warehouse_id,))
        row_s = cur.fetchone()
        current_stock = int(row_s["s"] or 0)


        # fetch purchase details
        cur.execute("""
            select purchaseDetail_id, product_id, quantity, received_qty
            from purchasedetail
            where purchase_id=%s
        """, (purchase_id,))
        details = cur.fetchall()

        # read received_now and capacity check
        total_received_now = 0
        received_map = {}

        for d in details:
            key = f"recv_{d['purchaseDetail_id']}"
            val = request.form.get(key, "").strip()
            recv_now = int(val) if val.isdigit() else 0

            remaining = int(d["quantity"]) - int(d["received_qty"])
            if recv_now < 0:
                recv_now = 0
            if recv_now > remaining:
                recv_now = remaining

            received_map[d["purchaseDetail_id"]] = recv_now
            total_received_now += recv_now

        if capacity == 0:
            return redirect(f"/purchases/receive/{purchase_id}?error=" + quote("Warehouse capacity is 0."))

        if current_stock + total_received_now > capacity:
            remaining_space = capacity - current_stock
            return redirect(
                f"/purchases/receive/{purchase_id}?error=" +
                quote(f"Capacity exceeded. Space left: {max(0, remaining_space)}")
            )

        #  apply updates + inventory + stock movement
        for d in details:
            recv_now = received_map[d["purchaseDetail_id"]]
            if recv_now == 0:
                continue

            # update purchasedetail
            cur.execute("""
                update purchasedetail
                set received_qty = received_qty + %s,arrival_date = NOW()
                where purchaseDetail_id=%s
            """, (recv_now, d["purchaseDetail_id"]))

            # inventory 
            cur.execute("""
                select inventory_id
                from inventory
                where warehouse_id=%s and product_id=%s
            """, (warehouse_id, d["product_id"]))
            inv = cur.fetchone()

            if inv:
                cur.execute("""
                    update inventory
                    set stock_quantity = stock_quantity + %s, last_updated = NOW()
                    where warehouse_id=%s and product_id=%s
                """, (recv_now, warehouse_id, d["product_id"]))
            else:
                cur.execute("""
                    insert into inventory (product_id, warehouse_id, stock_quantity, last_updated) values (%s, %s, %s, CURDATE())
                """, (d["product_id"], warehouse_id, recv_now))

            # stock movement
            cur.execute("""
                insert into stockMovment
                  (movement_date, movement_type, product_id, warehouse_id, staff_id, qty_change)
                values (NOW(), 'PURCHASE_RECEIVE', %s, %s, %s, %s)
            """, (d["product_id"], warehouse_id, staff_id, recv_now))

        # update statusP for all lines in this purchase
            cur.execute("""
              UPDATE purchasedetail
              SET statusP =
              CASE
              WHEN received_qty = 0 THEN 'Ordered'
              WHEN received_qty < quantity THEN 'Partial'
              ELSE 'Received'
              END
              WHERE purchase_id = %s
              """, (purchase_id,))


        conn.commit()
        return redirect(f"/purchases/receive/{purchase_id}?success=1")

    except Exception:
        conn.rollback()
        return redirect(f"/purchases/receive/{purchase_id}?error=" + quote("Receive failed."))

    finally:
        cur.close()
        conn.close()

########### ####
@app.route("/purchases", methods=["GET"])
def purchases_list():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
    select p.purchase_id,  p.purchase_date,  p.total_amount, p.invoice_number, s.supplier_name, b.nameBranch,
                case when
                COUNT(pd.purchaseDetail_id) = 0 then 'Draft' 
                WHEN SUM(pd.statusP = 'Received') = COUNT(*) THEN 'Received' 
                WHEN SUM(pd.statusP = 'Ordered') = COUNT(*) THEN 'Ordered'
                ELSE 'Partial' 
                END AS purchase_status
    from purchase p join supplier s on s.supplier_id = p.supplier_id join branch b on b.branch_id = p.branch_id join purchasedetail pd on pd.purchase_id = p.purchase_id
    group by p.purchase_id, p.purchase_date, p.total_amount, p.invoice_number, s.supplier_name, b.nameBranch
    order by p.purchase_id desc
    """)

    purchases = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("purchases/purchases_list.html", purchases=purchases)



##############################################################################################################################################

###################              ###             VIEW purchases               #################           ###          ###

###############################################################################################################################################3
@app.route("/purchases/view/<int:purchase_id>")
def purchase_view(purchase_id):

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
              SELECT p.purchase_id, p.total_amount, p.purchase_date, s.supplier_name, b.nameBranch, st.staff_id, st.first_name, st.last_name, st.phone
              FROM purchase p
              JOIN supplier s ON p.supplier_id = s.supplier_id
              JOIN branch b   ON p.branch_id = b.branch_id
              JOIN staff st   ON p.staff_id = st.staff_id
              WHERE p.purchase_id = %s;
              """, (purchase_id,))

    purchase = cur.fetchone()

    cur.execute("""
        select pr.product_name, pd.quantity, pd.unit_cost,(pd.quantity * pd.unit_cost) AS subtotal
        from purchasedetail pd JOIN product pr ON pr.product_id = pd.product_id
        where pd.purchase_id = %s
        """, (purchase_id,))
    items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("purchases/purchase_view.html",purchase=purchase,items=items)



#############################
                              
                             #############################
                                                          
                                                          #############################
                              
                             #############################
                                                          
                                                          #############################
                                                                                        
                             #############################
                                                          
                                                          #############################
                                                                                        
                             #############################
                                                          
                                                                                           #############################






##############################################################################################################################################

###################              ###            branches_list              #################           ###          ###

###############################################################################################################################################3                                                                                     
                                                                                                                                                        
@app.route("/branches", methods=["GET"])
def branches_list():
    city = request.args.get("city", "").strip()
    error = None

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if city:
        cur.execute("""
            SELECT branch_id, nameBranch, city, address, phone
            FROM branch
            WHERE city = %s
            ORDER BY nameBranch
        """, (city,))
    else:
        cur.execute("""
            SELECT branch_id, nameBranch, city, address, phone
            FROM branch
            ORDER BY nameBranch
        """)

    branches = cur.fetchall()
    cur.close()
    conn.close()

    return render_template( "branches/branches_list.html", branches=branches,city=city, error=error)
##############################################################################################################################################

###################              ###           NEW BRANCHES              #################           ###          ###

###############################################################################################################################################3   

@app.route("/branches/new", methods=["GET", "POST"])
def branch_new():
    if request.method == "POST":
        nameBranch = request.form.get("nameBranch", "").strip()
        city       = request.form.get("city", "").strip()
        address    = request.form.get("address", "").strip()
        phone      = request.form.get("phone", "").strip()
        back       = request.form.get("back", "/branches").strip()

        if not nameBranch or not phone:
            return render_template("branches/branch_form.html", error="Please fill required fields (Branch Name, Phone)",form=request.form, back=back )

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO branch (nameBranch, city, address, phone)
                VALUES (%s, %s, %s, %s)
            """, (nameBranch, city , address , phone))
            conn.commit()

        except Exception:
            conn.rollback()
            cur.close()
            conn.close()
            return render_template("branches/branch_form.html",error="Phone already exists or invalid data.", form=request.form,back=back)

        cur.close()
        conn.close()

        return redirect(back)


    back = request.args.get("back", "/branches").strip()
    return render_template("branches/branch_form.html", error=None, form=None, back=back)


##############################################################################################################################################

###################              ###           staff list              #################           ###          ###

###############################################################################################################################################3   

@app.route("/branches/<int:branch_id>/staff", methods=["GET"])
def staff_list(branch_id):
    search = request.args.get("search", "").strip()

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # fetch branch
    cur.execute("""
        SELECT branch_id, nameBranch, city
        FROM branch
        WHERE branch_id = %s
    """, (branch_id,))
    branch = cur.fetchone()

    if not branch:
        cur.close()
        conn.close()
        return redirect("/branches")

    
    if search:
        like = f"%{search}%"
        cur.execute("""
            SELECT staff_id, first_name, last_name, positionStaff, salary, phone, email
            FROM staff
            WHERE branch_id = %s
              AND (first_name LIKE %s OR last_name LIKE %s OR phone LIKE %s OR positionStaff LIKE %s)
            ORDER BY first_name, last_name
        """, (branch_id, like, like, like, like))# staff list sorted by name
    else:
        cur.execute("""
            SELECT staff_id, first_name, last_name, positionStaff, salary, phone, email
            FROM staff
            WHERE branch_id = %s
            ORDER BY first_name, last_name
        """, (branch_id,))

    staff_rows = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("staff/staff_list.html",branch=branch,staff_list=staff_rows,search=search,error=None)
##############################################################################################################################################

###################              ###           staff_new             #################           ###          ###

###############################################################################################################################################3 
@app.route("/branches/<int:branch_id>/staff/new", methods=["GET", "POST"])
def staff_new(branch_id):

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT branch_id, nameBranch, city
        FROM branch
        WHERE branch_id = %s
    """, (branch_id,))
    branch = cur.fetchone()

    if not branch:
        cur.close(); conn.close()
        return redirect("/branches")

    if request.method == "POST":
        first_name    = request.form.get("first_name", "").strip()
        last_name     = request.form.get("last_name", "").strip()
        positionStaff = request.form.get("positionStaff", "").strip() or None
        salary        = request.form.get("salary", "").strip()
        phone         = request.form.get("phone", "").strip() or None
        email         = request.form.get("email", "").strip() or None
        hire_date     = request.form.get("hire_date", "").strip() or None
        back          = request.form.get("back", f"/branches/{branch_id}/staff").strip()

        if not first_name or not last_name:
            cur.close()
            conn.close()
            return render_template("staff/staff_form.html",branch=branch,error="Please fill required fields (First Name, Last Name).",form=request.form,back=back )

        salary_value = None
        if salary:
            try:
                salary_value = float(salary)
            except:
                cur.close()
                conn.close()
                return render_template("staff/staff_form.html",branch=branch,error="Salary must be a number.",form=request.form,back=back)

        try:
            cur.execute("""
                INSERT INTO staff (first_name, last_name, positionStaff, salary, email, phone, hire_date, branch_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (first_name, last_name, positionStaff, salary_value, email, phone, hire_date, branch_id))
            conn.commit()
        except Exception:
            conn.rollback()
            cur.close()
            conn.close()
            return render_template("staff/staff_form.html",branch=branch,error="Failed to add staff! Check data.",form=request.form, back=back)

        cur.close()
        conn.close()
        return redirect(back)

    back = request.args.get("back", f"/branches/{branch_id}/staff").strip()
    cur.close(); conn.close()
    return render_template("staff/staff_form.html", branch=branch, error=None, form=None, back=back)


##############################################################################################################################################

###################              ###           managers_list           #################           ###          ###

###############################################################################################################################################3 

@app.route("/branches/managers", methods=["GET"])
def managers_list():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT b.branch_id, b.nameBranch, b.city, s.staff_id, s.first_name, s.last_name, s.phone,s.salary
        FROM branch b JOIN staff s ON s.branch_id = b.branch_id
        WHERE s.positionStaff = 'Branch Manager'
        ORDER BY b.branch_id
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("branches/managers_list.html", rows=rows)

##############################################################################################################################################

###################              ###           New    warehouse       #################           ###          ###

###############################################################################################################################################3 
@app.route("/branches/<int:branch_id>/warehouse/new", methods=["GET", "POST"])
def warehouse_new(branch_id):

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""SELECT branch_id, nameBranch, city 
                    FROM branch 
                    WHERE branch_id=%s""", (branch_id,))
        branch = cur.fetchone()
        if not branch:
            return redirect("/branches")

        if request.method == "GET":
            cur.execute("""SELECT warehouse_id 
                        FROM warehouse
                         WHERE branch_id=%s 
                        """, (branch_id,))
            if cur.fetchone():
                return redirect(f"/branches/{branch_id}/warehouse/edit")

            back = request.args.get("back", "/branches").strip()
            return render_template("branches/warehouse_form.html", branch=branch, error=None, form=None, back=back)

        name_warehouse = request.form.get("name_warehouse", "").strip()
        location       = request.form.get("location", "").strip() or None
        capacity_str   = request.form.get("capacity", "").strip()
        back           = request.form.get("back", "/branches").strip()

        if not name_warehouse:
            return render_template("branches/warehouse_form.html", branch=branch,error="Warehouse name is required.", form=request.form, back=back)

        if capacity_str and not capacity_str.isdigit():
            return render_template("branches/warehouse_form.html", branch=branch,error="Capacity must be a number.", form=request.form, back=back)

        capacity = int(capacity_str) if capacity_str else None

        cur.execute("""SELECT warehouse_id 
                    FROM warehouse 
                    WHERE branch_id=%s """, (branch_id,))
        if cur.fetchone():
            return redirect(back)

        cur.execute("""
            INSERT INTO warehouse (name_warehouse, location, capacity, branch_id)
            VALUES (%s, %s, %s, %s)
        """, (name_warehouse, location, capacity, branch_id))

        conn.commit()
        return redirect(back)

    except Exception:
        conn.rollback()
        return render_template("branches/warehouse_form.html", branch=branch,
                               error="Failed to create warehouse. Check data.", form=request.form, back=back)

    finally:
        cur.close()
        conn.close()


##############################################################################################################################################

###################              ###           Edit    warehouse       #################           ###          ###

###############################################################################################################################################3 
@app.route("/branches/<int:branch_id>/warehouse/edit", methods=["GET", "POST"])
def warehouse_edit(branch_id):

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # branch
        cur.execute("""SELECT branch_id, nameBranch, city
                     FROM branch
                     WHERE branch_id=%s""", (branch_id,))
        branch = cur.fetchone()
        if not branch:
            return redirect("/branches")

        # warehouse
        cur.execute("""
            SELECT warehouse_id, name_warehouse, location, capacity
            FROM warehouse
            WHERE branch_id=%s
            LIMIT 1
        """, (branch_id,))
        wh = cur.fetchone()
        if not wh:
            return redirect(f"/branches/{branch_id}/warehouse/new")

        if request.method == "GET":
            back = request.args.get("back", "/branches").strip()
            return render_template("branches/warehouse_form.html", branch=branch, error=None, form=wh, back=back)

        name_warehouse = request.form.get("name_warehouse", "").strip()
        location       = request.form.get("location", "").strip() or None
        capacity_str   = request.form.get("capacity", "").strip()
        back           = request.form.get("back", "/branches").strip()

        if not name_warehouse:
            return render_template("branches/warehouse_form.html", branch=branch,error="Warehouse name is required", form=request.form, back=back)

        if capacity_str and not capacity_str.isdigit():
            return render_template("branches/warehouse_form.html", branch=branch,error="Capacity must be a number", form=request.form, back=back)

        capacity = int(capacity_str) if capacity_str else None

        cur.execute("""
            UPDATE warehouse
            SET name_warehouse=%s, location=%s, capacity=%s
            WHERE warehouse_id=%s
        """, (name_warehouse, location, capacity, wh["warehouse_id"]))

        conn.commit()
        return redirect(back)

    except Exception:
        conn.rollback()
        return render_template("branches/warehouse_form.html", branch=branch,error="Failed to update warehouse.", form=request.form, back=back)

    finally:
        cur.close()
        conn.close()
##############################################################################################################################################

###################              ###          category summary      #################           ###          ###

###############################################################################################################################################3 
@app.route("/branches/<int:branch_id>/category-summary", methods=["GET"])
def branch_category_summary(branch_id):

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
 
        cur.execute("SELECT branch_id, nameBranch, city FROM branch WHERE branch_id=%s", (branch_id,))
        branch = cur.fetchone()
        if not branch:
            return redirect("/branches")

      
        cur.execute("SELECT warehouse_id FROM warehouse WHERE branch_id=%s LIMIT 1", (branch_id,))
        wh = cur.fetchone()
        if not wh:
            return redirect(f"/branches/{branch_id}/warehouse/new?back=/branches")

        cur.execute("""
            SELECT sup.supplier_name, c.nameCat AS category_name,SUM(i.stock_quantity) AS total_qty
            FROM warehouse w 
             JOIN inventory i ON i.warehouse_id = w.warehouse_id
            JOIN product p ON p.product_id = i.product_id
            JOIN category c ON c.category_id = p.category_id
            JOIN supplier sup ON sup.supplier_id = p.supplier_id
            WHERE w.branch_id = %s
            GROUP BY sup.supplier_name, c.nameCat
            ORDER BY sup.supplier_name, c.nameCat
        """, (branch_id,))
        rows = cur.fetchall()

        return render_template("branches/category_summary.html", branch=branch, rows=rows)

    finally:
        cur.close()
        conn.close()



@app.route("/warehouse")
def warehouse_dashboard():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT  w.name_warehouse, SUM(i.stock_quantity) AS total_stock
        FROM warehouse w
        JOIN inventory i ON i.warehouse_id = w.warehouse_id
        GROUP BY w.warehouse_id, w.name_warehouse
        ORDER BY total_stock
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("warehouse_stock_chart.html",data=data)

if __name__ == "__main__":
    app.run(debug=True)
