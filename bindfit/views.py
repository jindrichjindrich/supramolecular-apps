import os
import string
import random
import datetime
import pandas as pd
import numpy  as np

from django.core.mail import send_mail

from rest_framework.views import APIView

from rest_framework.parsers import JSONParser, MultiPartParser 

from rest_framework.response import Response
from rest_framework import status

from haystack.query  import SearchQuerySet
from haystack.inputs import AutoQuery 

from django.contrib.sites.models import Site
from django.conf import settings

from . import models
from . import formatter
from . import functions
from .fitter import Fitter

import logging
logger = logging.getLogger('supramolecular')

class FitView(APIView):
    parser_classes = (JSONParser,)

    def post(self, request):
        """
        Request:
            data_id: string  Reference to input data to use

            params: {
                    k1: {
                        init:   float User guess of first parameter
                        bounds: array Bounds on parameter fit
                        }
                    k2: { ... }
                    ...
                    }

        Response:
            data_id:
            data:
                x:
                y:
            labels:
                data:
                    x:
                    y:

            fit:
                y:
                coeffs:
                molefrac:
                params: {
                        k1: dict    First parameter optimised results
                        k2: dict    Second parameter optimised results
                        ..: ...     ...
                        }
            qof:
                residuals:
                cov:
                cov_total:
                rms:
                rms_total:
            time:
            options:
                dilute:
        """

        logger.debug("FitView.post: called")

        # Parse request options
        fitter_name = request.data["fitter"]

        # Get input data to fit from database
        dilute = request.data["options"]["dilute"] # Dilution factor flag
                                                   # used for data retrieval
        data = models.Data.objects.get(id=request.data["data_id"]).to_dict(
                fitter=fitter_name,
                dilute=dilute)

        logger.debug("views.FitView: data.to_dict() after retrieving")
        logger.debug(data)

        datax = data["data"]["x"]
        datay = data["data"]["y"]

        # Parse params to appropriate types
        params = request.data["params"]
        for key in params:
            parsed = {
                    "init": float(params[key]["init"]),
                    "bounds": {
                        "min": float(params[key]["bounds"]["min"]) 
                               if params[key]["bounds"]["min"] is not None 
                               and params[key]["bounds"]["min"] != ""
                               else None,
                        "max": float(params[key]["bounds"]["max"])
                               if params[key]["bounds"]["max"] is not None 
                               and params[key]["bounds"]["max"] != ""
                               else None,
                        }
                    }

            params[key].update(parsed)
            
        logger.debug("views.FitView: params parsed:")
        logger.debug(params)

        # "Normalise" y data flag, i.e. subtract initial values from y data 
        # (silly name choice, sorry)
        normalise = request.data["options"].get("normalise", True)
        # Chosen fitter "flavour" option if given
        flavour   = request.data["options"].get("flavour",   "")
        # Chosen fitter method if given
        method    = request.data["options"].get("method",    "")

        # Create and run appropriate fitter
        fitter = self.create_fitter(fitter_name, datax, datay, normalise, flavour)
        fitter.run_scipy(params, method=method)
        
        # Build response dict
        response = self.build_response(fitter_name, fitter, data, 
                                       dilute, normalise, method, flavour)
        return Response(response)

    @staticmethod
    def build_response(fitter_name, fitter, data, 
                       dilute, normalise, method, flavour):
        # Combined fitter and data dictionaries
        response = formatter.fit(fitter      =fitter_name,
                                 data        =data,
                                 y           =fitter.fit,
                                 params      =fitter.params,
                                 residuals   =fitter.residuals,
                                 coeffs_raw  =fitter.coeffs_raw,
                                 molefrac_raw=fitter.molefrac_raw,
                                 coeffs      =fitter.coeffs,
                                 molefrac    =fitter.molefrac,
                                 time        =fitter.time,
                                 dilute      =dilute,
                                 normalise   =normalise,
                                 method      =method,
                                 flavour     =flavour)
        return response

    @staticmethod
    def create_fitter(fitter_name, datax, datay, normalise, flavour="", params=None):
        # Initialise Fitter with approriate objective function
        function = functions.construct(fitter_name, normalise=normalise, flavour=flavour)
        fitter = Fitter(datax, datay, function, 
                        normalise=normalise, 
                        params=params)
        return fitter



class FitMonteCarloView(APIView):
    parser_classes = (JSONParser,)

    def post(self, request):
        """
        Calculate Monte Carlo error on fit. Accepts standard fit_result json
        as input, returns updated params object.
        """

        logger.debug("FitMonteCarloView.post: called")

        fit            = request.data["fit"]
        mc_n_iter      = request.data["options"]["n_iter"]
        mc_xdata_error = request.data["options"]["xdata_error"]
        mc_ydata_error = request.data["options"]["ydata_error"]

        fitter_name       = fit["fitter"]
        data_id           = fit["data_id"]
        options_dilute    = fit["options"]["dilute"]
        options_normalise = fit["options"].get("normalise", True)
        options_flavour   = fit["options"].get("flavour",   "")
        options_method    = fit["options"].get("method",    "")
        fit_params        = fit["fit"]["params"]

        logger.debug("FitMonteCarloView.post: received fit flavour")
        logger.debug(options_flavour)

        # Get data for fitting
        data = models.Data.objects.get(id=data_id).to_dict(
                fitter=fitter_name,
                dilute=options_dilute)
        datax = data["data"]["x"]
        datay = data["data"]["y"]

        # Create fitter w/ pre-set optimised parameter values
        fitter = FitView.create_fitter(fitter_name, datax, datay, 
                                       normalise=options_normalise, 
                                       flavour=options_flavour,
                                       params=fit_params)

        logger.debug("FitMonteCarloView.post: fitter created, flavour")
        logger.debug(fitter.function.flavour)

        # Calculate Monte Carlo
        logger.debug("FitMonteCarloView.post: calculating Monte Carlo error with n_iter, xdata, ydata:")
        logger.debug(mc_n_iter)
        logger.debug(mc_xdata_error)
        logger.debug(mc_ydata_error)
        params_updated = fitter.calc_monte_carlo(mc_n_iter, 
                                                 mc_xdata_error, 
                                                 mc_ydata_error,
                                                 method=options_method)

        # Build response dict
        response = params_updated
        return Response(response)



class FitOptionsView(APIView):
    parser_classes = (JSONParser,)

    def post(self, request):
        return Response(formatter.options(request.data["fitter"]))



class FitLabelsView(APIView):
    parser_classes = (JSONParser,)
    
    def post(self, request):
        return Response(formatter.labels(request.data["fitter"]))



class FitListView(APIView):
    parser_classes = (JSONParser,)
    
    def get(self, request):
        return Response(formatter.fitter_list())



class FitSaveView(APIView):
    parser_classes = (JSONParser,)

    def post(self, request):
        fit  = request.data
        meta = request.data["meta"]

        meta_options_searchable = meta["options"]["searchable"]

        meta_email     = meta.get("email",     "")
        meta_author    = meta.get("author",    "")
        meta_name      = meta.get("name",      "")
        meta_date      = meta.get("date",      None)
        meta_ref       = meta.get("ref",       "")
        meta_host      = meta.get("host",      "")
        meta_guest     = meta.get("guest",     "")
        meta_solvent   = meta.get("solvent",   "")
        meta_temp      = meta.get("temp",      None)
        meta_temp_unit = meta.get("temp_unit", None)
        meta_notes     = meta.get("notes",     "")

        # Hack to deal with receiving "None" string
        if meta_temp == "None" or meta_temp == "":
            meta_temp = None

        if meta_date == "None" or meta_date == "":
            meta_date = None

        options_fitter  = fit["fitter"]
        options_data_id = fit["data_id"]

        data = models.Data.objects.get(id=options_data_id)

        no_fit = fit["no_fit"]

        if not no_fit:
            options_dilute    = fit["options"]["dilute"]
            options_normalise = fit["options"]["normalise"]
            options_method    = fit["options"]["method"]
            options_flavour   = fit["options"]["flavour"]

            fit_params        = fit["fit"]["params"]
            fit_params_keys   = [ key for key in sorted(fit_params) ]
            fit_params_init   = [ fit_params[key]["init"]  
                                  for key in sorted(fit_params) ]
            # Convert bare float values to arrays here for DB storage
            fit_params_value  = [ fit_params[key]["value"]
                                  if isinstance(fit_params[key]["value"], list) 
                                  else [fit_params[key]["value"]]
                                  for key in sorted(fit_params) ]
            # Convert bare float values to arrays here for DB storage
            fit_params_stderr = [ fit_params[key]["stderr"]
                                  if isinstance(fit_params[key]["stderr"], list) 
                                  else [fit_params[key]["stderr"]]
                                  for key in sorted(fit_params) ]
            fit_params_bounds = [ [fit_params[key]["bounds"]["min"],
                                   fit_params[key]["bounds"]["max"]]
                                  for key in sorted(fit_params) ]

            fit_y      = fit["fit"]["y"]

            fit_molefrac     = fit["fit"]["molefrac"]
            fit_coeffs       = fit["fit"]["coeffs"]
            fit_molefrac_raw = fit["fit"]["molefrac_raw"]
            fit_coeffs_raw   = fit["fit"]["coeffs_raw"]
            fit_time         = fit["time"]
            fit_residuals    = fit["qof"]["residuals"]

            fit = models.Fit(no_fit=no_fit,
                             meta_options_searchable=meta_options_searchable, 
                             meta_email=meta_email, 
                             meta_author=meta_author, 
                             meta_name=meta_name, 
                             meta_date=meta_date, 
                             meta_ref=meta_ref, 
                             meta_host=meta_host, 
                             meta_guest=meta_guest, 
                             meta_solvent=meta_solvent, 
                             meta_temp=meta_temp, 
                             meta_notes=meta_notes,
                             data=data,
                             fitter_name=options_fitter,
                             options_dilute=options_dilute,
                             options_normalise=options_normalise,
                             options_method=options_method,
                             options_flavour=options_flavour,
                             fit_params_keys=fit_params_keys,
                             fit_params_init=fit_params_init,
                             fit_params_value=fit_params_value,
                             fit_params_stderr=fit_params_stderr,
                             fit_params_bounds=fit_params_bounds,
                             fit_y=fit_y,
                             fit_molefrac=fit_molefrac,
                             fit_coeffs=fit_coeffs,
                             fit_molefrac_raw=fit_molefrac_raw,
                             fit_coeffs_raw=fit_coeffs_raw,
                             qof_residuals=fit_residuals,
                             time=fit_time,
                             )
            fit.save()
        else:
            fit = models.Fit(no_fit=no_fit,
                             meta_options_searchable=meta_options_searchable, 
                             meta_email=meta_email, 
                             meta_author=meta_author, 
                             meta_name=meta_name, 
                             meta_date=meta_date, 
                             meta_ref=meta_ref, 
                             meta_host=meta_host, 
                             meta_guest=meta_guest, 
                             meta_solvent=meta_solvent, 
                             meta_temp=meta_temp, 
                             meta_notes=meta_notes,
                             data=data,
                             fitter_name=options_fitter,
                             )
            fit.save()

        response = formatter.save(fit.id)
        return Response(response)



class FitRetrieveView(APIView):
    parser_classes = (JSONParser,)

    def get(self, request, id):
        fit = models.Fit.objects.get(id=id)
        response = fit.to_dict()
        return Response(response)



class FitSearchEmailView(APIView):
    parser_classes = (JSONParser,)

    def post(self, request):
        view_url = request.data["view_url"] # Frontend view URL to use with fit IDs
        email    = request.data["email"]    # Email to retrieve fits for

        matches = models.Fit.objects.filter(meta_email=email)

        if matches:
            links = []
            for fit in matches:
                links.append(view_url+str(fit.id))

            body = "\n".join(links)

            send_mail("Your fit URLs", 
                      body, 
                      "BindFit Database <noreply@opendatafit.org>", 
                      [email], 
                      fail_silently=False)

            return Response({"detail": "Success! Check your email."}, 
                             status=status.HTTP_200_OK)
        else:
            # TODO return status here?
            return Response({"detail": "No matching fits found."}, 
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FitSearchView(APIView):
    parser_classes = (JSONParser,)

    def post(self, request):
        r = request.data

        if type(r['query']) is str:
            # Simple search - searches for matches in all indexed fields
            query = r['query']

            # TODO:
            # Shouldn't have to filter for searchable=True here as they
            # shouldn't be indexed in the first place, but for some reason 
            # RealtimeSignalProcessor doesn't listen to the index_queryset
            # filtering in search_indexes.py.
            # Filtering added here as a temp fix.
            matches = SearchQuerySet().filter(content=AutoQuery(query)).filter(searchable=True)

        elif type(r['query']) is dict:
            # Advanced search (not implemented)
            # TODO: port to haystack, expand
            # Current code gets only exact matches directly from the database
            query = r['query']

            # Parse request names -> DB field names
            search = {}
            for (key, value) in query.items():
                if value:
                    search["meta_"+str(key)] = value

            # Get matching entries from DB
            matches = models.Fit.objects.filter(**search)

        else:
            # Bad query
            return Response({"detail": "Query must be a string or object."}, 
                             status=status.HTTP_400_BAD_REQUEST)

        summary_list = []

        for match in matches.all():
            summary = match.object.summary
            summary_list.append(summary)

        response = {"matches": summary_list}

        return Response(response)
 


class FitExportView(APIView):
    parser_classes = (JSONParser,)
    
    def post(self, request):
        dt = 'f8'

        fit  = request.data
        meta = request.data["meta"]

        labels = formatter.labels(fit["fitter"])
        user_labels = fit["labels"]

        # Input options
        options_fitter = fit["fitter"]
        options_params = np.array(
                [ fit["fit"]["params"][key]["init"] 
                  for key in sorted(fit["fit"]["params"]) ], 
                dtype=dt)
        options_dilute    = fit["options"]["dilute"]
        options_normalise = fit["options"]["normalise"]
        options_method    = fit["options"]["method"]
        options_flavour   = fit["options"]["flavour"]

        # Construct fitter function for calculating formatted x
        function = functions.construct(options_fitter, 
                                       normalise=options_normalise,
                                       flavour=options_flavour)

        # Munge some data
        # Transpose 1D arrays -> 2D column arrays for hstack later
        # Input data
        data_x_labels = user_labels["data"]["x"]["row_labels"]
        data_y_labels = user_labels["data"]["y"]["row_labels"]
        data_x        = np.array(fit["data"]["x"],  dtype=dt).T
        data_x_calc   = function.format_x(np.array(fit["data"]["x"], 
                                                   dtype=dt))[np.newaxis].T
        data_y        = np.array(fit["data"]["y"],  dtype=dt).T


        # Fit results 
        fit_y          = np.array(fit["fit"]["y"],          dtype=dt).T
        fit_params     = np.array(
                [ fit["fit"]["params"][key]["value"][0] 
                    if isinstance(fit["fit"]["params"][key]["value"], list) 
                    else fit["fit"]["params"][key]["value"]
                  for key in sorted(fit["fit"]["params"]) ], 
                dtype=dt)
        fit_molefrac   = np.array(fit["fit"]["molefrac"],   dtype=dt).T
        fit_coeffs_raw = np.array(fit["fit"]["coeffs_raw"], dtype=dt).T
        fit_coeffs     = np.array(fit["fit"]["coeffs"],     dtype=dt).T
        # PLACEHOLDER  deal with multi-D y inputs here later
        fit_residuals  = np.array(fit["qof"]["residuals"],  dtype=dt).T
        fit_rms        = np.array(fit["qof"]["rms"],        dtype=dt).T
        fit_cov        = np.array(fit["qof"]["cov"],        dtype=dt).T
        fit_rms_total  = fit["qof"]["rms_total"]
        fit_cov_total  = fit["qof"]["cov_total"]

        # Labels
        params_labels_dict = labels["fit"]["params"]
        params_labels      = [ params_labels_dict[key] for key in sorted(params_labels_dict) ]
        coeffs_labels      = labels["fit"]["coeffs"]
        molefrac_labels    = labels["fit"]["molefrac"]

        # Create output arrays
        data_array     = np.hstack((data_x, data_x_calc, data_y))
        options_array  = np.concatenate(([options_fitter], options_params))
        fit_array      = np.hstack((data_x, data_x_calc, fit_y, fit_residuals, fit_molefrac))
        qof_array_1    = np.append(fit_rms, fit_rms_total)
        qof_array_2    = np.append(fit_cov, fit_cov_total)

        if len(fit_params.shape) < 2:
            # No sub-params
            params_array_1 = fit_params[np.newaxis] # To force horizontal array
                                                    # in DataFrame
        else:
            # Deal with sub-params (for now just take initial subparam from 
            # each group)
            params_array_1 = np.array([ p[0] for p in fit_params ])[np.newaxis]

        params_array_2 = fit_coeffs
        params_array_3 = fit_coeffs_raw

        # Generate appropriate column titles
        data_names      = [ "x"+str(i+1)+": "+l for i, l in enumerate(data_x_labels) ]
        data_names.extend(["x3: G/H equivalent total"])
        data_names.extend([ "y"+str(i+1)+": "+l for i, l in enumerate(data_y_labels) ])
        logger.debug("DATA_NAMES")
        logger.debug(data_names)

        options_names      = ["Fitter"]
        options_names.extend([ p["label"][0]
                                   if isinstance(p["label"], list)
                                   else p["label"]
                               for p in params_labels ])
        if len(options_names) > len(options_array):
            options_names = options_names[:len(options_array)]

        fit_names      = [ "x"+str(i+1)+": "+l for i, l in enumerate(data_x_labels) ]
        fit_names.extend(["x3: G/H equivalent total"])
        fit_names.extend([ "y"+str(i+1)+": "+l for i, l in enumerate(data_y_labels) ])
        fit_names.extend([ "y"+str(i+1)+": Residuals" for i in range(fit_residuals.shape[1]) ])
        fit_names.extend([ "y"+str(i+1)+": Molefractions" for i in range(fit_molefrac.shape[1]) ])
        logger.debug("FIT_NAMES")
        logger.debug(fit_names)

        qof_names_1 = [ "RMS: "+l for l in data_y_labels ]
        qof_names_1.append("RMS: Total")
        qof_names_2 = [ "Covariance: "+l for l in data_y_labels ]
        qof_names_2.append("Covariance: Total")

        params_names_1 = [ p["label"][0]
                               if isinstance(p["label"], list) 
                               else p["label"] 
                           for p in params_labels ]
        if len(params_names_1) > len(params_array_1[0]):
            params_names_1 = params_names_1[:len(params_array_1)]
        params_names_2 = [ str(l)+" coeffs" for l in coeffs_labels ]
        params_names_3 = [ "Raw coeffs"+str(i+1) for i in range(fit_coeffs_raw.shape[1]) ]

        # Create data frames for export
        data_output     = pd.DataFrame(data_array,     columns=data_names)
        options_output  = pd.DataFrame(options_array,  index=options_names) 
        fit_output      = pd.DataFrame(fit_array,      columns=fit_names)
        qof_output_1    = pd.DataFrame(qof_array_1,    index=qof_names_1)
        qof_output_2    = pd.DataFrame(qof_array_2,    index=qof_names_2)
        qof_output      = pd.concat([qof_output_1,
                                     qof_output_2],
                                     axis=0,
                                     join_axes=[qof_output_1.columns])
        params_output_1 = pd.DataFrame(params_array_1, columns=params_names_1)
        params_output_2 = pd.DataFrame(params_array_2, columns=params_names_2)
        params_output_3 = pd.DataFrame(params_array_3, columns=params_names_3)
        params_output   = pd.concat([params_output_1,
                                     params_output_2,
                                     params_output_3],
                                     axis=1,
                                     join_axes=[params_output_2.index])

        # Create export file
        # Randomly generate export filename
        filename = id_generator()+".xlsx"
        export_path = os.path.join(settings.MEDIA_ROOT, "output", filename) 

        # Write all dataframes to excel file
        writer = pd.ExcelWriter(export_path)
        data_output.to_excel(writer, "Input Data", index=False)
        options_output.to_excel(writer, "Input Options", header=False)
        params_output.to_excel(writer, "Output Parameters", index=False)
        fit_output.to_excel(writer, "Output Fit", index=False)
        qof_output.to_excel(writer, "Output Fit Quality", header=False)
        writer.save()

        export_url = settings.ROOT_URL+settings.MEDIA_URL+"output/"+filename

        return Response(formatter.export(export_url))



class UploadDataView(APIView):
    """
    Request:

    Response:
        string: Name of uploaded file on server
    """

    REQUEST_KEY = "input"

    parser_classes = (MultiPartParser, )

    def put(self, request):
        # Read file
        f = request.FILES[self.REQUEST_KEY]

        ext    = os.path.splitext(str(f))[1][1:] # file extension
        fitter = request.data["fitter"]          # selected fitter key

        if ext == "csv":
            d = models.Data.from_csv(fitter, f)
        elif ext == "xls" or ext == "xlsx":
            d = models.Data.from_xls(fitter, f)
        else:
            # Try reading from csv as default if no extension provided
            d = models.Data.from_csv(fitter, f)

        d.save()

        logger.debug("UploadDataView.put: received fitter key")
        logger.debug(fitter)

        # Return parsed data
        response = d.to_dict(fitter=fitter, dilute=False)
        return Response(response, status=200)



#
# Helper functions
#

def id_generator(size=5, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
    # Generates random ID from a given list of characters
    # Used for random filenames on exporting
    return "".join(random.choice(chars) for _ in range(size))
