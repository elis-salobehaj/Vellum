package main

import (
	"context"

	"github.com/crossplane/function-sdk-go"
	"github.com/crossplane/function-sdk-go/errors"
	"github.com/crossplane/function-sdk-go/logging"
	fnv1 "github.com/crossplane/function-sdk-go/proto/v1"
	"github.com/crossplane/function-sdk-go/request"
	"github.com/crossplane/function-sdk-go/response"
)

func main() {
	if err := function.Serve(&Function{}); err != nil {
		panic(err)
	}
}

type Function struct {
	fnv1.UnimplementedFunctionRunnerServiceServer
}

func (f *Function) RunFunction(_ context.Context, req *fnv1.RunFunctionRequest) (*fnv1.RunFunctionResponse, error) {
	log := logging.NewNopLogger()
	rsp := response.To(req, response.DefaultTTL)

	// Get all desired composed resources
	desired, err := request.GetDesiredComposedResources(req)
	if err != nil {
		response.Fatal(rsp, errors.Wrapf(err, "cannot get desired composed resources"))
		return rsp, nil
	}

	// Iterate over desired resources and add a label
	for name, dr := range desired {
		log.Info("Processing resource", "name", name)
		
		// Add the label
		labels := dr.Resource.GetLabels()
		if labels == nil {
			labels = map[string]string{}
		}
		labels["vellum.io/managed-by"] = "crossplane-go"
		dr.Resource.SetLabels(labels)
	}

	// Set the updated resources back in the response
	if err := response.SetDesiredComposedResources(rsp, desired); err != nil {
		response.Fatal(rsp, errors.Wrapf(err, "cannot set desired composed resources"))
		return rsp, nil
	}

	log.Info("Successfully processed resources", "count", len(desired))
	return rsp, nil
}
