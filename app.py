import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates
from starlette_admin.contrib.sqla import Admin, ModelView

from login import UsernameAndPasswordProvider
from models import engine, User, Salon, Barber, Appointment, Service, BarberAvailability, BarberService

app = Starlette()

# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Admin setup
admin = Admin(engine, title="Example: SQLAlchemy",
              base_url='/',
              auth_provider=UsernameAndPasswordProvider(),
              middlewares=[Middleware(SessionMiddleware, secret_key="qewrerthytju4")],
              )

# Adding User Model to Admin
admin.add_view(ModelView(User, icon='fas fa-user'))
admin.add_view(ModelView(Salon, icon='fas fa-user'))
admin.add_view(ModelView(Barber, icon='fas fa-user'))
admin.add_view(ModelView(Appointment, icon='fas fa-user'))
admin.add_view(ModelView(Service, icon='fas fa-user'))
admin.add_view(ModelView(BarberAvailability, icon='fas fa-user'))
admin.add_view(ModelView(BarberService, icon='fas fa-user'))

admin.mount_to(app)

# Run the app
if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8050)
